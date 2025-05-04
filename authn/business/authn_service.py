from authn.persistence.authn_repository import AuthnRepository

class AuthnService:
    authn_repository = AuthnRepository()

    def get_authn_by_student_number(self, student_number: str):
        return self.authn_repository.get_authn_by_student_number(student_number)

    def get_authn_user_id_by_student_number(self, student_number: str):
        return self.authn_repository.get_authn_user_id_by_student_number(student_number)
    
    def get_authn_by_user_id(self, user_id: str):
        return self.authn_repository.get_authn_by_user_id(user_id)