from cabinet.persistence.cabinet_repository import CabinetRepository
from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

from authn.business.authn_service import AuthnService

authn_service = AuthnService()

cabinet_repository = CabinetRepository()
cabinet_history_repository = CabinetHistoryRepository()

class CabinetHistoryService :
    def get_cabinet_histories_by_student_number(self, student_number : str):

        user_id = authn_service.get_authn_user_id_by_student_number(student_number)

        return cabinet_history_repository.get_cabinet_histories_by_user_id(user_id)