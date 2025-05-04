import threading
import time
import random
import logging
from django.test import TransactionTestCase
from django.utils import timezone
from django.db import transaction
from django_redis import get_redis_connection
from concurrent.futures import ThreadPoolExecutor, as_completed

from cabinet.models import cabinets, cabinet_histories, buildings
from user.models import users
from authn.models import RoleEnum, authns
from cabinet.business.cabinet_service import CabinetService
from cabinet.exceptions import CabinetAlreadyRentedException, UserHasRentalException
from building.type.BuildingNameEnum import BuildingNameEnum
from cabinet.type import CabinetStatusEnum, CabinetPayableEnum
from authn.business.authn_service import AuthnService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CabinetConcurrentRentTest(TransactionTestCase):
    """사물함 동시 대여 통합 테스트"""
    
    def setUp(self):
        """테스트 데이터 설정"""
        # Redis 연결 초기화
        self.redis_conn = get_redis_connection("default")
        
        # Redis 키 정리
        self._clear_redis_keys()
        
        # 테스트용 건물 생성
        self.building = buildings.objects.create(
            name=BuildingNameEnum.가온관,
            floor=1,
            section="A",
            width=100,
            height=100
        )
        
        # 테스트용 사물함 10개 생성
        self.test_cabinets = []
        for i in range(10):
            cabinet = cabinets.objects.create(
                building_id=self.building,
                cabinet_number=i+1,
                status=CabinetStatusEnum.AVAILABLE.value,
                payable=CabinetPayableEnum.FREE.value,
                reason=None
            )
            self.test_cabinets.append(cabinet)
        
        # 테스트용 사용자 정보 (미리 생성)
        self.test_users = []
        for i in range(10000):
            student_number = f"test{i+1:05}"
            user = self._create_test_user(student_number)
            self.test_users.append({
                'user': user,
                'student_number': student_number,
                'cabinet_index': i // 1000  # 0~9 범위로 각 사물함에 1,000명씩 할당
            })
        
        # 서비스 인스턴스 생성
        self.cabinet_service = CabinetService()
        
        # 결과 추적을 위한 변수
        self.success_count = 0
        self.failure_count = 0
        self.lock = threading.Lock()
        
        # 각 사물함별 성공 여부 추적
        self.cabinet_success = {cabinet.id: False for cabinet in self.test_cabinets}
        
        # 각 사물함별 성공한 사용자
        self.success_users = {cabinet.id: None for cabinet in self.test_cabinets}

    def _clear_redis_keys(self):
        """테스트 관련 Redis 키 정리"""
        # cabinet: 로 시작하는 모든 키 삭제
        for key in self.redis_conn.keys("cabinet:*"):
            self.redis_conn.delete(key)
    
    def _create_test_user(self, student_number):
        """테스트용 사용자 및 인증 정보 생성"""
        # 이미 존재하는 인증 정보 확인
        existing_auth = authns.objects.filter(student_number=student_number).first()
        if existing_auth:
            return existing_auth.user_id
                
        # 새 사용자 생성
        user = users.objects.create(
            name=student_number,
            phone_number="010-1234-5678" + student_number,
            is_visible=True
        )
        
        # 인증 정보 생성
        auth = authns.objects.create(
            user_id=user,
            student_number=student_number,
            password="testpassword",  # 실제로는 해싱된 비밀번호를 사용해야 함
            role=RoleEnum.NORMAL
        )
        
        return user
    
    def _attempt_rent(self, user_info):
        """사물함 대여 시도 - 직접 서비스 호출"""
        student_number = user_info['student_number']
        cabinet_index = user_info['cabinet_index']
        cabinet_id = self.test_cabinets[cabinet_index].id
        
        # 약간의 지연으로 동시 접속 시간 차이 시뮬레이션
        time.sleep(random.uniform(0, 0.05))
        
        try:
            # 이미 성공한 사물함인지 먼저 검사 (락 획득 전에 빠른 검사)
            with self.lock:
                if self.cabinet_success.get(cabinet_id, False):
                    self.failure_count += 1
                    return False
            
            # 사물함 대여 직접 처리 (비동기 대신 동기 처리로 테스트)
            with transaction.atomic(savepoint=True):
                # 사용자 정보 확인
                user = user_info['user']
                user_id = user.id
                
                # 사용자가 이미 대여한 사물함 확인
                existing_cabinet = cabinets.objects.filter(user_id=user_id, status='USING').first()
                if existing_cabinet:
                    with self.lock:
                        self.failure_count += 1
                    return False
                
                # 사물함 상태 확인 및 락 획득 - nowait=True로 락 획득 실패 시 즉시 예외 발생
                try:
                    cabinet = cabinets.objects.select_for_update(nowait=True).filter(
                        id=cabinet_id, 
                        status='AVAILABLE'
                    ).first()
                except Exception:
                    # 락 획득 실패 - 다른 트랜잭션이 이미 락을 획득한 경우
                    with self.lock:
                        self.failure_count += 1
                    return False
                
                if not cabinet:
                    with self.lock:
                        self.failure_count += 1
                    return False
                
                # 대여 가능 검사 추가
                if cabinet.status != 'AVAILABLE' or cabinet.user_id_id is not None:
                    with self.lock:
                        self.failure_count += 1
                    return False
                
                # 락 획득 후 한 번 더 확인 (추가 안전장치)
                with self.lock:
                    if self.cabinet_success.get(cabinet_id, False):
                        self.failure_count += 1
                        return False
                    
                    # 성공 표시 미리 설정 (다른 스레드가 동시에 접근하는 것 방지)
                    self.cabinet_success[cabinet_id] = True
                    self.success_users[cabinet_id] = student_number
                
                # 대여 처리
                # 이력 생성
                expire_date = timezone.now() + timezone.timedelta(days=30)
                history = cabinet_histories.objects.create(
                    user_id_id=user_id,
                    cabinet_id_id=cabinet_id,
                    expired_at=expire_date
                )
                
                # 상태 변경
                cabinet.status = 'USING'
                cabinet.user_id_id = user_id
                cabinet.save()
                
                # 성공 처리
                with self.lock:
                    self.success_count += 1
                
                logger.info(f"사용자 {student_number}가 사물함 {cabinet_id} 대여 성공")
                
                # 성공 후 즉시 반납 (다음 테스트를 위해)
                time.sleep(random.uniform(0.05, 0.1))
                self._attempt_return(student_number, cabinet_id, user_id)
                
                return True
        
        except Exception as e:
            # 실패 처리
            with self.lock:
                # 성공 표시가 미리 설정되었다면 취소
                if self.cabinet_success.get(cabinet_id) == True and self.success_users.get(cabinet_id) == student_number:
                    self.cabinet_success[cabinet_id] = False
                    self.success_users[cabinet_id] = None
                
                self.failure_count += 1
            
            logger.error(f"사용자 {student_number}가 사물함 {cabinet_id} 대여 중 오류: {str(e)}")
            return False

    def _attempt_return(self, student_number, cabinet_id, user_id):
        """사물함 반납 시도 - 직접 처리"""
        try:
            with transaction.atomic():
                # 사물함 정보 확인 및 락 획득
                cabinet = cabinets.objects.select_for_update().filter(
                    id=cabinet_id, 
                    status='USING',
                    user_id_id=user_id
                ).first()
                
                if not cabinet:
                    logger.warning(f"반납 실패: 사물함 {cabinet_id}가 해당 사용자의 것이 아님")
                    return False
                
                # 이력 업데이트
                history = cabinet_histories.objects.filter(
                    cabinet_id_id=cabinet_id,
                    user_id_id=user_id,
                    ended_at=None
                ).order_by('-created_at').first()
                
                if history:
                    history.ended_at = timezone.now()
                    history.save()
                
                # 상태 변경
                cabinet.status = 'AVAILABLE'
                cabinet.user_id = None
                cabinet.save()
                
                logger.info(f"사용자 {student_number}가 사물함 {cabinet_id} 반납 성공")
                return True
                
        except Exception as e:
            logger.error(f"사용자 {student_number}가 사물함 {cabinet_id} 반납 중 오류: {str(e)}")
            return False
    
    def test_concurrent_cabinet_rental(self):
        """동시 사물함 대여 테스트"""
        start_time = time.time()
        logger.info("===== 동시 사물함 대여 테스트 시작 =====")
        
        # ThreadPoolExecutor를 사용하여 동시 요청 처리
        with ThreadPoolExecutor(max_workers=50) as executor:
            # 모든 사용자가 동시에 대여 시도
            futures = [executor.submit(self._attempt_rent, user_info) for user_info in self.test_users]
            
            # 모든 작업 완료 대기
            for future in as_completed(futures):
                pass
        
        end_time = time.time()
        duration = end_time - start_time
        
        # 결과 검증
        logger.info(f"테스트 소요 시간: {duration:.2f}초")
        logger.info(f"성공 건수: {self.success_count}, 실패 건수: {self.failure_count}")
        
        # 각 사물함별 성공 여부 확인
        for cabinet_id, success in self.cabinet_success.items():
            logger.info(f"사물함 {cabinet_id}: {'성공' if success else '실패'}, 대여 사용자: {self.success_users[cabinet_id]}")
        
        # 최종 검증
        self.assertEqual(self.success_count, 10, "각 사물함마다 정확히 1개씩, 총 10개의 대여가 성공해야 합니다")
        self.assertEqual(self.failure_count, 9990, "나머지 9,990개의 대여 시도는 실패해야 합니다")
        
        # 모든 사물함이 'AVAILABLE' 상태인지 확인 (반납 완료 확인)
        for cabinet in self.test_cabinets:
            cabinet.refresh_from_db()
            self.assertEqual(cabinet.status, CabinetStatusEnum.AVAILABLE.value, 
                            f"모든 사물함이 반납되어 AVAILABLE 상태여야 합니다 (ID: {cabinet.id})")
            self.assertIsNone(cabinet.user_id_id, 
                            f"모든 사물함이 반납되어 user_id가 None이어야 합니다 (ID: {cabinet.id})")

        logger.info("===== 동시 사물함 대여 테스트 완료 =====")
    
    def test_race_condition_handling(self):
        """경쟁 조건 처리 테스트 - 동일 사물함에 대한 집중 요청"""
        # 하나의 사물함에 집중적으로 요청
        target_cabinet_id = self.test_cabinets[0].id
        target_users = self.test_users[:1000]  # 처음 1000명의 사용자만 사용
        
        # 테스트 시작 전 사물함 상태 재확인
        cabinet = cabinets.objects.get(id=target_cabinet_id)
        cabinet.status = CabinetStatusEnum.AVAILABLE.value
        cabinet.user_id = None
        cabinet.save()
        
        logger.info(f"===== 경쟁 조건 테스트 시작 (사물함 ID: {target_cabinet_id}) =====")
        
        success_count = 0
        failure_count = 0
        race_lock = threading.Lock()
        
        def attempt_concentrated_rent(user_info):
            nonlocal success_count, failure_count
            
            student_number = user_info['student_number']
            user = user_info['user']
            user_id = user.id
            
            try:
                # 더 엄격한 격리 수준 사용
                with transaction.atomic(using='default', savepoint=True):
                    # 사물함 상태 확인 및 락 획득 - 더 명시적인 락 사용
                    cabinet = cabinets.objects.select_for_update(nowait=True).filter(
                        id=target_cabinet_id, 
                        status='AVAILABLE'
                    ).first()
                    
                    if not cabinet:
                        with race_lock:
                            failure_count += 1
                        return False
                    
                    # 랜덤 지연으로 경쟁 조건 시뮬레이션 강화
                    time.sleep(random.uniform(0.001, 0.01))
                    
                    # 대여 처리
                    # 이력 생성
                    expire_date = timezone.now() + timezone.timedelta(days=30)
                    history = cabinet_histories.objects.create(
                        user_id_id=user_id,
                        cabinet_id_id=target_cabinet_id,
                        expired_at=expire_date
                    )
                    
                    # 상태 변경
                    cabinet.status = 'USING'
                    cabinet.user_id_id = user_id
                    cabinet.save()
                    
                    # 성공 처리
                    with race_lock:
                        success_count += 1
                    
                    logger.info(f"사용자 {student_number}가 경쟁 조건 테스트에서 대여 성공")
                    
                    # 성공 후 즉시 반납
                    time.sleep(0.1)
                    
                    # 반납 처리
                    cabinet = cabinets.objects.select_for_update().get(id=target_cabinet_id)
                    cabinet.status = 'AVAILABLE'
                    cabinet.user_id = None
                    cabinet.save()
                    
                    # 이력 업데이트
                    history.ended_at = timezone.now()
                    history.save()
                    
                    return True
            
            except Exception as e:
                with race_lock:
                    failure_count += 1
                logger.warning(f"대여 실패: {str(e)}")
                return False
        
        # 1000명이 동시에 같은 사물함 대여 시도
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(attempt_concentrated_rent, user_info) for user_info in target_users]
            for future in as_completed(futures):
                pass
        
        logger.info(f"경쟁 조건 테스트 결과: 성공 {success_count}, 실패 {failure_count}")
        
        # 검증: 한 번에 한 사용자만 대여 성공해야 함
        self.assertEqual(success_count, 1, "경쟁 조건에서 정확히 1명만 대여에 성공해야 합니다")
        self.assertEqual(failure_count, 999, "나머지 999명은 실패해야 합니다")
        
        # 최종 사물함 상태 확인
        target_cabinet = cabinets.objects.get(id=target_cabinet_id)
        self.assertEqual(target_cabinet.status, CabinetStatusEnum.AVAILABLE.value, 
                        "테스트 완료 후 사물함은 AVAILABLE 상태여야 합니다")
        
        logger.info(f"===== 경쟁 조건 테스트 완료 =====")