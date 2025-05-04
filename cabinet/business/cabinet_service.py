import logging
import time
from cabinet.exceptions import CabinetAlreadyRentedException, CabinetNotFoundException, CabinetRentFailedException, CabinetReturnFailedException, UserHasRentalException
from cabinet.persistence.cabinet_repository import CabinetRepository
from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

from authn.business.authn_service import AuthnService
from core.exception.exceptions import GlobalRedisLockException
from user.exceptions import UserNotFoundException

from django.db import transaction
from django_redis import get_redis_connection
from cabinet.util.cabinet_kafka_rent_producer import CabinetRentProducer
from core.config.redis_lock import RedisLock
from cabinet.util.worker_pool import CabinetThreadPool

from cabinet.util.cabinet_async_result_manager import AsyncResultManager

authn_service = AuthnService()

cabinet_repository = CabinetRepository()
cabinet_history_repository = CabinetHistoryRepository()

logger = logging.getLogger(__name__)

class CabinetService :
    """사물함 서비스"""
    
    def get_cabinets_by_building_ids(self, building_id: int):
        """건물 ID로 사물함 목록 조회"""
        return cabinet_repository.get_cabinets_by_building_ids(building_id)

    def get_cabinet_by_id(self, cabinet_id: int):
        """사물함 ID로 정보 조회"""
        return cabinet_repository.get_cabinet_by_id(cabinet_id)

    def request_rent_cabinet(self, cabinet_id: int, student_number: str, check_result=True):
        """사물함 대여 요청 - 완전 비동기 방식"""
        redis_conn = get_redis_connection("default")
        processing_key = f"cabinet:processing:{cabinet_id}"
        status_key = f"cabinet:status:{cabinet_id}"

        # 이미 처리 중인지 확인
        if redis_conn.get(processing_key):
            raise CabinetRentFailedException(cabinet_id)

        try:
            # 처리 중으로 표시
            redis_conn.set(processing_key, student_number, ex=15)
            redis_conn.set(status_key, f"renting:{student_number}", ex=60)
            
            # 기본 검증 (가벼운 검증만 수행)
            user_auth_info = authn_service.get_authn_by_student_number(student_number)
            if not user_auth_info:
                redis_conn.delete(processing_key)
                redis_conn.delete(status_key)
                raise UserNotFoundException(student_number=student_number)
                
            # 비동기 작업 ID 생성
            task_id = f"rental-{int(time.time())}-{cabinet_id}-{student_number}"
            
            # 1. 스레드 풀 작업 등록
            thread_pool = CabinetThreadPool()
            thread_pool.start()
            thread_pool.add_rental_task(cabinet_id, student_number, task_id)
            logger.info(f"사물함 {cabinet_id} 대여 작업이 스레드 풀에 추가됨 (작업 ID: {task_id})")
            
            # 2. Celery 작업 등록 (백업)
            try:
                from cabinet.util.cabinet_celery_task import process_cabinet_rental
                celery_task = process_cabinet_rental.delay(cabinet_id, student_number, task_id)
                logger.info(f"Celery 대여 작업 등록 완료 (작업 ID: {celery_task.id})")
            except Exception as e:
                logger.warning(f"Celery 작업 등록 건너뜀: {str(e)}")
            
            # 3. Kafka 메시지 발행 (추가 백업)
            try:
                producer = CabinetRentProducer()
                if producer.available:
                    producer.send_rental_request(cabinet_id, student_number)
                    logger.info(f"Kafka 메시지 전송 완료 (사물함 ID: {cabinet_id})")
            except Exception as e:
                logger.warning(f"Kafka 메시지 전송 건너뜀: {str(e)}")
            
            # 비동기 작업 결과 확인 (API 호출에서만)
            if check_result and task_id:
                result = AsyncResultManager.get_result(task_id, timeout=5)
                
                # 결과가 없으면 진행 중 상태로 응답
                if not result:
                    return {
                        'message': '사물함 대여 요청이 처리 중입니다.',
                        'task_id': task_id,
                        'status': 'processing'
                    }
                
                # 결과에 따라 처리
                if result.get("status") == "success":
                    # 성공 시 상태 업데이트 후 결과 반환
                    redis_conn.set(status_key, f"rented:{student_number}", ex=3600)
                    return {
                        'message': '사물함 대여가 완료되었습니다.',
                        'cabinet_id': cabinet_id,
                        'status': 'success'
                    }
                else:
                    # 실패 시 상태 제거 및 예외 발생
                    redis_conn.delete(status_key)
                    exception_class = result.get("exception_class", "")
                    message = result.get("message", "알 수 없는 오류가 발생했습니다")
                    
                    # 예외 유형에 따라 적절한 예외 발생
                    if "UserHasRental" in exception_class:
                        raise UserHasRentalException(student_number=student_number)
                    elif "CabinetAlreadyRented" in exception_class:
                        raise CabinetAlreadyRentedException(cabinet_id=cabinet_id)
                    elif "CabinetNotFound" in exception_class:
                        raise CabinetNotFoundException(cabinet_id=cabinet_id)
                    else:
                        raise CabinetRentFailedException(cabinet_id=cabinet_id)
            
            # 결과 확인하지 않는 경우 (비동기 처리만 시작)
            return {
                'message': '사물함 대여 요청이 처리되고 있습니다.',
                'task_id': task_id,
                'status': 'accepted'
            }
        except Exception as e:
            # 모든 오류 상황에서 상태 키 제거
            redis_conn.delete(status_key)
            logger.error(f"대여 요청 처리 중 오류: {str(e)}")
            raise
        finally:
            # 처리 중 키는 항상 삭제하지 않음 (비동기 처리가 진행 중이므로)
            # 실제 처리 메서드에서 삭제하도록 함
            pass
    
    @transaction.atomic
    def rent_cabinet(self, cabinet_id: int, student_number: str):
        """
        사물함 대여 처리 (실제 DB 반영)
        """
        # 락 획득
        lock_name = f"cabinet:{cabinet_id}:rent"
        try:
            with RedisLock(lock_name, expire_time=30) as lock:
                if not lock.acquired:
                    raise GlobalRedisLockException("사물함 대여 처리를 위한 락을 획득할 수 없습니다")
                    
                # 사용자 정보 조회
                user_auth_info = authn_service.get_authn_by_student_number(student_number)
                if not user_auth_info:
                    raise UserNotFoundException(student_number=student_number)
                    
                # 사용자가 이미 대여한 사물함 확인
                existing_cabinet = cabinet_repository.get_cabinet_by_user_id(user_auth_info.user_id)
                if existing_cabinet and existing_cabinet.status == 'USING':
                    raise UserHasRentalException(student_number=student_number)

                # 사물함 조회
                cabinet = cabinet_repository.get_cabinet_by_id(cabinet_id)
                if not cabinet:
                    raise CabinetNotFoundException(cabinet_id=cabinet_id)
                    
                # 대여 가능 상태 확인
                if cabinet.status != 'AVAILABLE':
                    raise CabinetAlreadyRentedException(cabinet_id=cabinet_id)

                # 캐비넷 대여 이력 생성
                cabinet_history_repository.rent_cabinet(cabinet, user_auth_info.user_id)

                # 캐비넷 상태 변경 (DB 반영)
                cabinet_repository.update_cabinet_status(cabinet_id, user_auth_info.user_id, 'USING')
                
                # 성공적으로 DB 업데이트 완료
                logger.info(f"사물함 {cabinet_id} 대여 완료 (사용자: {student_number})")
                return cabinet
        except Exception as e:
            # 롤백 발생 시 로그
            logger.error(f"사물함 대여 실패 (트랜잭션 롤백): {str(e)}")
            raise

    @transaction.atomic
    def return_cabinet(self, cabinet_id: int, student_number: str):
        """사물함 반납 처리 (동기 방식)"""
        redis_conn = get_redis_connection("default")
        status_key = f"cabinet:status:{cabinet_id}"
        processing_key = f"cabinet:processing:{cabinet_id}"
        
        # 대여 진행 중인지 먼저 확인
        status = redis_conn.get(status_key)
        if status and status.decode('utf-8').startswith('renting:'):
            # 대여 진행 중이면 완료될 때까지 대기 (최대 5초)
            wait_start = time.time()
            while time.time() - wait_start < 5:
                # 상태 다시 확인
                status = redis_conn.get(status_key)
                if not status or not status.decode('utf-8').startswith('renting:'):
                    break
                time.sleep(0.2)  # 200ms 대기
        
        # 대여 상태 확인
        status = redis_conn.get(status_key)
        # 아직도 대여 진행 중이면 오류
        if status and status.decode('utf-8').startswith('renting:'):
            raise CabinetReturnFailedException(cabinet_id=cabinet_id)
        
        # DB에서도 대여 상태 확인
        try:
            cabinet = cabinet_repository.get_cabinet_by_id(cabinet_id)
            if not cabinet:
                raise CabinetNotFoundException(cabinet_id=cabinet_id)
                
            if cabinet.status != 'USING':
                # DB에는 대여 상태가 아니지만 Redis에는 대여 완료 표시가 있는 경우
                if status and status.decode('utf-8').startswith('rented:'):
                    # Redis 정보를 신뢰하고 사용자에게 알림
                    extracted_student = status.decode('utf-8').split(':')[1]
                    if extracted_student == student_number:
                        # 상태 불일치 로그 남기고 진행
                        logger.warning(f"사물함 {cabinet_id} 상태 불일치: Redis=rented, DB={cabinet.status}")
                        # 여기서 DB 동기화 시도할 수 있음
                    else:
                        raise CabinetReturnFailedException(cabinet_id=cabinet_id)
                else:
                    raise CabinetReturnFailedException(cabinet_id=cabinet_id)
        except CabinetReturnFailedException:
            raise
        except CabinetNotFoundException:
            raise
        except Exception as e:
            logger.error(f"사물함 {cabinet_id} 조회 실패: {str(e)}")
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        
        # 반납 처리 락 획득
        lock_name = f"cabinet:{cabinet_id}:return"
        with RedisLock(lock_name, expire_time=10) as lock:
            if not lock.acquired:
                raise GlobalRedisLockException("사물함 반납 처리를 위한 락을 획득할 수 없습니다")

            # 사용자 정보 조회
            user_auth_info = authn_service.get_authn_by_student_number(student_number)
            if not user_auth_info:
                raise UserNotFoundException(student_number=student_number)

            cabinet_repository.check_valid_return(user_auth_info.user_id, cabinet_id)
            
            # 캐비넷 반납 이력 생성 - NULL 오류 해결
            try:
                cabinet_history_repository.return_cabinet(cabinet, user_auth_info.user_id)
            except Exception as e:
                logger.error(f"사물함 이력 생성 실패: {str(e)}")
                # 이력 생성 실패해도 상태 변경은 진행

            # 캐비넷 상태 변경
            cabinet_repository.update_cabinet_status(cabinet_id, user_id=None, status='AVAILABLE')
            
            # Redis 상태 업데이트
            redis_conn.delete(status_key)
            redis_conn.delete(processing_key)
            
            # Celery 작업 취소 시도 (이미 진행 중인 작업이 있다면)
            try:
                # 관련 스레드 풀 작업 결과 정리
                AsyncResultManager.set_result(f"rental-*-{cabinet_id}-*", {
                    "status": "cancelled",
                    "message": f"사물함 {cabinet_id}가 수동으로 반납되었습니다."
                })
                
                # Kafka 메시지 발행 (반납 완료 알림)
                try:
                    producer = CabinetRentProducer()
                    if producer.available:
                        producer.send_return_request(cabinet_id, student_number)
                except Exception as e:
                    logger.warning(f"Kafka 반납 완료 메시지 전송 실패: {str(e)}")
            except Exception as e:
                logger.warning(f"비동기 작업 정리 실패: {str(e)}")
                
            return cabinet


    def search_cabinet(self, keyword : str):
        if keyword.isdigit():
            return cabinet_repository.get_cabinets_exact_match_by_cabinet_number(int(keyword))
        else:
            return cabinet_repository.get_cabinets_contains_by_building_name(keyword)
        
    def get_all_cabinets(self):
        return cabinet_repository.get_all_cabinets()
    
    def return_cabinets_by_ids(self, cabinet_ids : list):
        return cabinet_repository.return_cabinets_by_ids(cabinet_ids)
    
    def assign_cabinet_to_user(self, cabinet_id : int, student_number : str, status : str):
        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number)

        return cabinet_repository.assign_cabinet_to_user(cabinet_id, user_auth_info, status)
    
    def change_cabinet_status_by_ids(self, cabinet_ids : list, new_status : str, reason : str):
        return cabinet_repository.change_cabinet_status_by_ids(cabinet_ids, new_status, reason)
    
    def get_cabinet_statistics(self):
        return cabinet_repository.get_cabinet_statistics()
    
    def get_cabinets_by_status(self, status : str):
        return cabinet_repository.get_cabinets_by_status(status)