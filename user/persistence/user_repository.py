
from user.models import users

from django.utils import timezone

class UserRepository:
    def get_user_by_student_number(self, student_number):
        return users.objects.filter(authn_info__student_number=student_number).first()
    
    def update_user_is_visible_by_student_number(self, student_number, is_visible):
        return users.objects.update(is_visible=is_visible, updated_at=timezone.now())