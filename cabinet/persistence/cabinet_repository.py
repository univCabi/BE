from django.utils import timezone
from cabinet.models import cabinets
from django.db.models import Count, Case, When
from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, CabinetNotRentedException, CabinetReturnFailedException, CabinetStatusUpdateException, UserHasRentalException, CabinetReturnException

from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository
from cabinet.type import CabinetStatusEnum

cabinet_history_repository = CabinetHistoryRepository()

from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException

class CabinetRepository:
    def get_cabinets_by_building_ids(self, building_ids):
        return cabinets.objects.filter(
            building_id__in=building_ids
        ).select_related('user_id', 'cabinet_positions', 'building_id')
    
    def get_cabinet_by_id(self, cabinet_id : int):
        return cabinets.objects.filter(id=cabinet_id).select_related('user_id', 'cabinet_positions', 'building_id').first()

    #TODO: 이력 조회를 위한 메소드로 변경함에 따라 이후 로직 변경
    def check_valid_rental(self, user_id : int, cabinet_id : int):
        if cabinet_history_repository.get_renting_cabinet_history_by_user_id(user_id) is None :
            raise UserHasRentalException()

        if cabinet_history_repository.get_renting_cabinet_history_by_cabinet_id(cabinet_id) is not None :
            raise CabinetAlreadyRentedException(cabinet_id=cabinet_id)
        
        if self.get_cabinet_by_id(cabinet_id=cabinet_id) is None :
            raise CabinetNotFoundException(cabinet_id=cabinet_id)

    #TODO: 이력 조회를 위한 메소드로 변경함에 따라 이후 로직 변경
    def check_valid_return(self, user_id : int, cabinet_id : int):

        if cabinet_history_repository.get_using_cabinet_info(user_id=user_id, cabinet_id=cabinet_id) is None:
            raise CabinetNotRentedException(cabinet_id=cabinet_id)
        
        if self.get_cabinet_by_id(cabinet_id=cabinet_id) is None :
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        
    def update_cabinet_status(self, cabinet_id : int, user_id : int, status : str):
        result =  cabinets.objects.filter(id=cabinet_id).update(
            status=status, 
            user_id_id=user_id,
            updated_at=timezone.now()
        )

        if not result:
            raise CabinetStatusUpdateException(cabinet_id=cabinet_id)
        return result
    
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
                cabinet = self.get_cabinet_by_id(cabinet_id)
                if not cabinet:
                    raise CabinetNotFoundException(cabinet_id=cabinet_id)
                
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
                    cabinet.refresh_from_db()
                    successful_cabinets.append(cabinet)
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
                cabinet = self.get_cabinet_by_id(cabinet_id)
                
                if not cabinet:
                    failed_ids.append({
                        "id": cabinet_id,
                        "reason": "사물함을 찾을 수 없습니다."
                    })
                    continue
                
                # 단일 사물함 상태 변경 처리
                updated_cabinet = self.update_cabinet_status_with_history(
                    cabinet, new_status, reason
                )
                
                successful_cabinets.append(updated_cabinet)
                
            except Exception as e:
                failed_ids.append({
                    "id": cabinet_id,
                    "reason": str(e)
                })
        
        return successful_cabinets, failed_ids
    
    def update_cabinet_status_with_history(self, cabinet, new_status, reason=''):
        # 상태별 처리 로직 분리 호출
        if new_status == "BROKEN":
            self.handle_broken_status(cabinet, reason)
        elif new_status == "AVAILABLE":
            self.handle_available_status(cabinet, cabinet.user_id)
        
        # DB 업데이트 (save 호출 대신 update 사용)
        self.update_cabinet_status_and_reason(cabinet)
        
        return cabinet

    def handle_broken_status(self, cabinet, reason):
        current_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
        if current_history:
            self.update_cabinet_history_ended(current_history)

    def handle_available_status(self, cabinet, old_user):
        current_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
        if current_history:
            self.update_cabinet_history_ended(current_history)
        
        # 사용자 정보 초기화
        cabinet.reason = None
        cabinet.user_id = None
        
        # 사용자가 있었다면 반납 처리
        if old_user:
            try:
                cabinet_history_repository.return_cabinet(cabinet, old_user)
            except CabinetReturnFailedException:
                # 이미 반납된 경우 무시 (히스토리에서 이미 처리됨)
                pass

    def update_cabinet_history_ended(self, history):
        history.ended_at = timezone.now()
        history.updated_at = timezone.now()
        result = history.save(update_fields=['ended_at', 'updated_at'])

        if not result:
            raise CabinetReturnException(cabinet_id=history.cabinet_id.id)
        return result

    def update_cabinet_status_and_reason(self, cabinet):
        """
        캐비닛 변경사항 저장 (save 대신 update 사용)
        """
        # update 메소드 사용하여 DB 직접 업데이트
        result = cabinets.objects.filter(id=cabinet.id).update(
            status=cabinet.status,
            reason=cabinet.reason,
            user_id=cabinet.user_id,
            updated_at=timezone.now()
        )

        if not result:
            raise CabinetStatusUpdateException(cabinet_id=cabinet.id)
        return result
        

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
            cabinet = self.get_cabinet_by_id(cabinet_id)
            
            if not cabinet:
                failed_ids.append({
                    "id": cabinet_id,
                    "reason": "사물함을 찾을 수 없습니다."
                })
                return successful_cabinets, failed_ids
            
            # 사물함 할당 처리 로직 호출
            updated_cabinet = self.assign_cabinet(cabinet, user_auth_info.user_id, status)
            successful_cabinets.append(updated_cabinet)
            
        except Exception as e:
            failed_ids.append({
                "id": cabinet_id,
                "reason": str(e)
            })
        
        return successful_cabinets, failed_ids

    def assign_cabinet(self, cabinet, user_id, status="USING"):
        """
        사물함을 사용자에게 할당하고 관련 히스토리를 생성합니다.
        
        Args:
            cabinet: 할당할 사물함 객체
            user_id: 할당 대상 사용자 ID
            status: 변경할 상태 (USING 또는 OVERDUE)
            
        Returns:
            업데이트된 사물함 객체
        """
        # 기존에 사용 중인 히스토리가 있는지 확인
        current_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
        
        # 사용 중인 기록이 있다면 종료 처리
        if current_history:
            self.update_cabinet_history_ended(current_history)
        
        # 사물함 정보 업데이트
        self.update_cabinet_assignment(cabinet, user_id, status)
        
        # 상태에 따른 히스토리 생성
        self.create_cabinet_history(cabinet, user_id, status)
        
        return cabinet

    def update_cabinet_assignment(self, cabinet, user_id, status):
        """
        사물함 할당 정보를 업데이트합니다.
        
        Args:
            cabinet: 업데이트할 사물함 객체
            user_id: 할당 대상 사용자 ID
            status: 변경할 상태
        """
        # 메모리 상의 객체 업데이트
        cabinet.user_id = user_id
        cabinet.status = status
        
        # DB 직접 업데이트 (save 대신 update 사용)
        cabinets.objects.filter(id=cabinet.id).update(
            user_id=user_id,
            status=status,
            reason=None,
            updated_at=timezone.now()
        )
        
        # 메모리 객체의 updated_at 필드도 업데이트
        cabinet.updated_at = timezone.now()

    def create_cabinet_history(self, cabinet, user_id, status):
        """
        상태에 따른 적절한 사물함 히스토리를 생성합니다.
        
        Args:
            cabinet: 사물함 객체
            user_id: 사용자 ID
            status: 변경할 상태
        """
        if status == "OVERDUE":
            # OVERDUE 상태일 경우 만료된 히스토리 생성
            cabinet_history_repository.rent_cabinet_overdue(cabinet, user_id)
        else:
            # 일반적인 대여 히스토리 생성
            cabinet_history_repository.rent_cabinet(cabinet, user_id)
    
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

    def get_cabinet_by_user_id(self, user_id):
        """
        특정 사용자가 대여한 사물함을 조회합니다.
        """
        return cabinets.objects.filter(user_id=user_id).first()