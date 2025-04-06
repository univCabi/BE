
from authn.business.authn_service import AuthnService
from cabinet.exceptions import CabinetNotFoundException
from cabinet.persistence.cabinet_bookmark_repository import CabinetBookmarkRepository
from cabinet.persistence.cabinet_repository import CabinetRepository
from user.exceptions import UserNotFoundException

authn_service = AuthnService()

cabinet_bookmark_repository = CabinetBookmarkRepository()
cabinet_repository = CabinetRepository()

class CabinetBookmarkService :
    def add_bookmark(self, cabinet_id, student_number):
        # 사용자 정보 조회

        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number=student_number)
        
        cabinet_info = cabinet_repository.get_cabinet_by_id(cabinet_id) 

        if not cabinet_info:
            raise CabinetNotFoundException(cabinet_id=cabinet_id)

        return cabinet_bookmark_repository.add_bookmark(user_info=user_auth_info, cabinet_info=cabinet_info)
    
    def remove_bookmark(self, cabinet_id, student_number):

        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number=student_number)
        
        cabinet_info = cabinet_repository.get_cabinet_by_id(cabinet_id) 

        if not cabinet_info:
            raise CabinetNotFoundException(cabinet_id=cabinet_id)

        return cabinet_bookmark_repository.remove_bookmark(user_info=user_auth_info, cabinet_info=cabinet_info)
    
    def get_bookmarks(self, student_number):

        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number=student_number)
        

        return cabinet_bookmark_repository.get_bookmarks(user_info=user_auth_info)