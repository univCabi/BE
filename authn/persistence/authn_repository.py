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