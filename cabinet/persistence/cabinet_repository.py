from django.utils import timezone
from cabinet.models import cabinets
from django.db.models import Count, Case, When
from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException, CabinetReturnException

from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

cabinet_history_repository = CabinetHistoryRepository()

from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException

class CabinetRepository:
    def get_cabinets_by_building_ids(self, building_ids):
        """
        여러 건물 ID를 받아 해당하는 캐비넷 목록을 반환
        """
        cabinet_qs = cabinets.objects.filter(
            building_id__in=building_ids
        ).select_related('user_id', 'cabinet_positions')

        if not cabinet_qs.exists():
            raise CabinetNotFoundException(building_ids=building_ids)
            
        return cabinet_qs
    
    def get_cabinet_by_id(self, cabinet_id : int):
        cabinet = cabinets.objects.filter(id=cabinet_id).select_related('user_id', 'cabinet_positions').first()

        if not cabinet:
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        return cabinet
    
    def check_valid_rental(self, user_id : int, cabinet_id : int):
        # 1. 사용자가 이미 다른 캐비넷을 대여했는지 확인
        try :
            if cabinet_history_repository.get_renting_cabinet_history_by_user_id(user_id) :
                raise UserHasRentalException()
        except CabinetNotFoundException:
            pass

        # 2. 해당 캐비넷이 이미 대여 중인지 확인
        try :
            if cabinet_history_repository.get_renting_cabinet_history_by_cabinet_id(cabinet_id):
                raise CabinetAlreadyRentedException(cabinet_id=cabinet_id)
        except CabinetNotFoundException:
            pass
        
        # 3. 캐비넷이 존재하는지 확인
        cabinet = cabinets.objects.get(id=cabinet_id)
        if not cabinet :
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        return cabinet
    
    def check_valid_return(self, user_id : int, cabinet_id : int):
        # 1. 사용자가 해당 캐비넷을 대여했는지 확인
        if not cabinet_history_repository.get_using_cabinet_info(user_id=user_id, cabinet_id=cabinet_id):
            raise UserHasRentalException(user_id=user_id)
        
        # 2. 캐비넷이 존재하는지 확인
        cabinet = cabinets.objects.get(id=cabinet_id)
        if not cabinet :
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        return cabinet
        
    def update_cabinet_status(self, cabinet_id : int, user_id : int, status : str):
        return cabinets.objects.filter(id=cabinet_id).update(
            status=status, 
            user_id_id=user_id,
            updated_at=timezone.now()
        )
    
    def get_cabinets_exact_match_by_cabinet_number(self, cabinet_number : int):
        return cabinets.objects.filter(cabinet_number__exact=cabinet_number)
    
    def get_cabinets_contains_by_building_name(self, building_name : str):
        return cabinets.objects.filter(building_id__name__contains=building_name)
    
    def get_all_cabinets(self) :
        return cabinets.objects.all().order_by('id')
    
    def return_cabinets_by_ids(self, cabinet_ids: list):
        """
        특정 ID 목록의 사물함을 반납처리하고 성공/실패한 캐비닛 정보 반환
        """
        failed_ids = []
        successful_cabinets = []
        
        for cabinet_id in cabinet_ids:
            try:
                # 먼저 해당 ID의 캐비닛이 존재하는지 확인
                cabinet = cabinets.objects.get(id=cabinet_id)
                
                # USING 또는 OVERDUE 상태인지 확인
                if cabinet.status not in ['USING', 'OVERDUE'] or not cabinet.user_id:
                    failed_ids.append({
                        'id': cabinet_id,
                        'reason': '반납 가능한 상태(USING 또는 OVERDUE)가 아닙니다'
                    })
                    continue
                    
                # 활성 대여 이력 종료
                cabinet_history_repository.return_cabinet(cabinet, cabinet.user_id)
            
                # 사물함 상태 업데이트
                updated = self.update_cabinet_status(cabinet_id, None, 'AVAILABLE')
                
                if updated:
                    # 업데이트 후 최신 상태의 캐비닛 객체 가져오기
                    updated_cabinet = cabinets.objects.select_related('building_id').get(id=cabinet_id)
                    successful_cabinets.append(updated_cabinet)
                else:
                    failed_ids.append({
                        'id': cabinet_id, 
                        'reason': '업데이트 실패'
                    })
                    
            except cabinets.DoesNotExist:
                failed_ids.append({
                    'id': cabinet_id, 
                    'reason': '해당 ID의 사물함이 존재하지 않습니다'
                })
        
        return successful_cabinets, failed_ids
    
    def change_cabinet_status_by_ids(self, cabinet_ids, new_status, reason=''):
        """
        관리자용: 여러 사물함의 상태를 변경합니다.
        
        Args:
            cabinet_ids: 상태를 변경할 사물함 ID 목록
            new_status: 변경할 상태 (AVAILABLE, BROKEN)
            reason: 상태 변경 사유 (BROKEN 상태일 때 필수)
            
        Returns:
            successful_cabinets: 성공적으로 상태가 변경된 사물함 목록
            failed_ids: 상태 변경에 실패한 사물함 ID와 실패 사유
        """
        successful_cabinets = []
        failed_ids = []
        
        for cabinet_id in cabinet_ids:
            try:
                # 사물함 조회
                cabinet = cabinets.objects.filter(id=cabinet_id).first()
                
                if not cabinet:
                    failed_ids.append({
                        "id": cabinet_id,
                        "reason": "사물함을 찾을 수 없습니다."
                    })
                    continue
                
                old_status = cabinet.status
                old_user = cabinet.user_id
                
                # 상태 변경
                cabinet.status = new_status
                
                # 히스토리 처리
                #current_history = cabinet_histories.objects.filter(
                #    cabinet_id=cabinet,
                #    ended_at__isnull=True
                #).first()

                current_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
                
                # 상태별 처리
                if new_status == "BROKEN":
                    cabinet.reason = reason
                    
                    # 사용 중이었다면 히스토리 종료
                    if current_history:
                        current_history.ended_at = timezone.now()
                        current_history.save()
                        
                        # BROKEN 상태의 새 히스토리 추가 (필요시)
                        # 관리자 조치로 인한 BROKEN 상태 기록
                        # cabinet_histories.objects.create(
                        #     user_id=old_user,  # 마지막 사용자 기록 유지 또는 None
                        #     cabinet_id=cabinet,
                        #     expired_at=timezone.now() + timezone.timedelta(days=0),  # 만료일 없음
                        #     ended_at=None  # 수리될 때까지 열린 상태로 유지
                        # )
                    
                elif new_status == "AVAILABLE":
                    # 기존 히스토리 종료
                    if current_history:
                        current_history.ended_at = timezone.now()
                        current_history.updated_at = timezone.now()
                        current_history.save()
                    
                    # 사용자 정보 초기화
                    cabinet.reason = None
                    cabinet.user_id = None
                    
                    # cabinet_history_repository를 통한 반납 처리
                    if old_user:
                        cabinet_history_repository.return_cabinet(cabinet, old_user)
                
                # 사물함 저장
                cabinet.save()
                successful_cabinets.append(cabinet)
                
            except Exception as e:
                failed_ids.append({
                    "id": cabinet_id,
                    "reason": str(e)
                })
        
        return successful_cabinets, failed_ids

    def assign_cabinet_to_user(self, cabinet_id, user_auth_info, status="USING"):
        """
        관리자용: 사물함을 특정 사용자에게 할당합니다.
        
        Args:
            cabinet_id: 할당할 사물함 ID
            user_auth_info: 사용자 인증 정보 객체
            status: 변경할 상태 (USING 또는 OVERDUE)
            
        Returns:
            successful_cabinets: 성공적으로 할당된 사물함
            failed_ids: 할당 실패 정보
        """
        successful_cabinets = []
        failed_ids = []
        
        try:
            # 사물함 조회
            cabinet = cabinets.objects.filter(id=cabinet_id).first()
            
            if not cabinet:
                failed_ids.append({
                    "id": cabinet_id,
                    "reason": "사물함을 찾을 수 없습니다."
                })
                return successful_cabinets, failed_ids
            
            user = user_auth_info.user_id
            
            # 사물함 상태 업데이트
            cabinet.user_id = user
            cabinet.status = status
            cabinet.save()

            # 상태에 따라 적절한 사물함 히스토리 생성
            if status == "OVERDUE":
                # OVERDUE 상태일 경우 현재 시간을 기준으로 ended_at과 expired_at 설정
                cabinet_history_repository.rent_cabinet_overdue(cabinet, user)
            else:
                # 일반적인 대여 시에는 기존 메소드 사용
                cabinet_history_repository.rent_cabinet(cabinet, user)
            
            successful_cabinets.append(cabinet)
            
        except Exception as e:
            failed_ids.append({
                "id": cabinet_id,
                "reason": str(e)
            })
        
        return successful_cabinets, failed_ids
    
    def get_cabinet_statistics(self):
        """
        건물별 사물함 상태 통계를 가져옵니다.
        """
        building_stats = cabinets.objects.select_related('building_id').values(
            'building_id__name'
        ).annotate(
            total=Count('id'),
            using=Count(Case(When(status='USING', then=1))),
            available=Count(Case(When(status='AVAILABLE', then=1))),
            broken=Count(Case(When(status='BROKEN', then=1))),
            overdue=Count(Case(When(status='OVERDUE', then=1)))
        ).order_by('building_id__name')
        
        result = []
        for stat in building_stats:
            result.append({
                'name': stat['building_id__name'] or '미지정',
                'total': stat['total'],
                'using': stat['using'],
                'overdue': stat['overdue'],
                'broken': stat['broken'],
                'available': stat['available']  # 'AVAILABLE' 상태는 'returned'와 동일
            })
        
        return result
    
    def get_cabinets_by_status(self, status_param):
        """
        특정 상태의 사물함 목록을 조회합니다.
        """
        # 해당 상태의 모든 사물함 조회
        cabinets_qs = cabinets.objects.filter(
            status=status_param
        ).select_related('building_id', 'user_id')
        
        if not cabinets_qs.exists():
            raise CabinetNotFoundException()
        
        results = []
        for cabinet in cabinets_qs:
            cabinet_data = {
                'id': cabinet.id,
                'building': cabinet.building_id.name if cabinet.building_id else None,
                'floor': cabinet.building_id.floor if cabinet.building_id else None,
                'section': cabinet.building_id.section if hasattr(cabinet.building_id, 'section') else None,
                'position': {
                    'x': cabinet.cabinet_positions.cabinet_x_pos,
                    'y': cabinet.cabinet_positions.cabinet_y_pos
                } if hasattr(cabinet, 'cabinet_positions') and cabinet.cabinet_positions else None,
                'cabinetNumber': cabinet.cabinet_number,
                'status': cabinet.status,
                'reason': cabinet.reason,
                'user': None,
            }
            
            # 사용자 정보 추가 (사용중인 경우)
            if cabinet.user_id:
                user = cabinet.user_id
                cabinet_data['user'] = {
                    'studentNumber': user.student_number if hasattr(user, 'student_number') else None,
                    'name': user.name if hasattr(user, 'name') else None
                }
            
            # 상태별 추가 정보
            if status_param == 'OVERDUE':
                rental_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
                
                if rental_history:
                    cabinet_data['rentalStartDate'] = rental_history.created_at
                    cabinet_data['overDate'] = rental_history.expired_at
            
            elif status_param == "BROKEN":
                # BROKEN 상태일 때 날짜 처리 방식 수정
                # 1. 먼저 현재 사용 중인 히스토리가 있는지 확인
                current_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
                
                if current_history:
                    cabinet_data['rentalStartDate'] = current_history.created_at
                
                # 2. 항상 cabinet의 updated_at을 brokenDate로 사용 (BROKEN으로 상태가 변경된 시점)
                cabinet_data['brokenDate'] = cabinet.updated_at
            
            results.append(cabinet_data)
        
        return results    
