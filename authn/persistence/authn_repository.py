from authn.models import authns

from cabinet.exceptions import CabinetNotFoundException

class AuthnRepository:
    def get_authn_by_student_number(self, student_number : str):
        authn = authns.objects.filter(student_number=student_number).first()

        if not authn:
            raise CabinetNotFoundException(student_number=student_number)
        return authn
    
    def get_authn_user_id_by_student_number(self, student_number : str):
        authn = authns.objects.filter(student_number=student_number).first()

        if not authn:
            raise CabinetNotFoundException(student_number=student_number)
        return authn.user_id
    
    def get_authn_by_user_id(self, user_id : str):
        authn = authns.objects.filter(user_id=user_id).first()

        if not authn:
            raise CabinetNotFoundException(user_id=user_id)
        return authn