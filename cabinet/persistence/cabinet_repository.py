from cabinet.models import cabinets
from cabinet.models import cabinet_histories
from django.utils import timezone
from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException, CabinetReturnException

from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

cabinet_history_repository = CabinetHistoryRepository()

from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException

class CabinetRepository:
    def get_cabinets_by_building_id(self, building_id : int):
        cabinet_qs = cabinets.objects.filter(building_id=building_id).select_related('user_id', 'cabinet_positions')

        if not cabinet_qs.exists():
            raise CabinetNotFoundException(building_id=building_id)
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
                raise UserHasRentalException(user_id=user_id)
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
            user_id_id=user_id
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