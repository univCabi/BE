from cabinet.persistence.cabinet_repository import CabinetRepository
from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

from authn.business.authn_service import AuthnService

authn_service = AuthnService()

cabinet_repository = CabinetRepository()
cabinet_history_repository = CabinetHistoryRepository()

class CabinetService :
    def get_cabinets_by_building_ids(self, building_id : int):
        return cabinet_repository.get_cabinets_by_building_ids(building_id)

    def get_cabinet_by_id(self, cabinet_id : int):
        return cabinet_repository.get_cabinet_by_id(cabinet_id)
    
    def rent_cabinet(self, cabinet_id : int, student_number : str):

        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        # 캐비넷 대여 가능 여부 확인
        cabinet = cabinet_repository.check_valid_rental(user_auth_info.user_id, cabinet_id)

        # 캐비넷 대여
        cabinet_history_repository.rent_cabinet(cabinet, user_auth_info.user_id)

        # 캐비넷 상태 변경
        cabinet_repository.update_cabinet_status(cabinet_id, user_auth_info.user_id, 'USING')

    def return_cabinet(self, cabinet_id : int, student_number : str):

        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        # 캐비넷 반납 가능 여부 확인
        cabinet = cabinet_repository.check_valid_return(user_auth_info.user_id, cabinet_id)

        # 캐비넷 반납
        cabinet_history_repository.return_cabinet(cabinet, user_auth_info.user_id)

        # 캐비넷 상태 변경
        cabinet_repository.update_cabinet_status(cabinet_id, user_id=None, status='AVAILABLE')

    def search_cabinet(self, keyword : str):
        if keyword.isdigit():
            return cabinet_repository.get_cabinets_exact_match_by_cabinet_number(int(keyword))
        else:
            return cabinet_repository.get_cabinets_contains_by_building_name(keyword)
        
    def get_all_cabinets(self):
        return cabinet_repository.get_all_cabinets()
    
    def return_cabinets_by_ids(self, cabinet_ids : list):
        return cabinet_repository.return_cabinets_by_ids(cabinet_ids)
    
    def change_cabinet_status_by_ids(self, cabinet_ids : list, new_status : str, reason : str):
        return cabinet_repository.change_cabinet_status_by_ids(cabinet_ids, new_status, reason)
    
    def get_cabinet_statistics(self):
        return cabinet_repository.get_cabinet_statistics()
    
    def get_cabinets_by_status(self, status : str):
        return cabinet_repository.get_cabinets_by_status(status)