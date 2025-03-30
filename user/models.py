from django.db import models
from django.utils import timezone

from building.models import buildings

class users(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    affiliation = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, unique=True)
    building_id = models.ForeignKey(buildings, on_delete=models.SET_NULL, null=True, related_name='building_info')
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.id})"  # name과 id를 사용하여 문자열 반환

    @classmethod
    def find_one_userinfo_by_id(cls, id):
        return cls.objects.get_or_create(id=id)
    
    @classmethod
    def find_one_userinfo_by_student_number(cls, student_number):
        return cls.objects.get(authn_info__student_number=student_number)

    @classmethod
    def update_user_is_visible_by_student_number(cls, student_number, is_visible):
        
        return cls.objects.update(is_visible=is_visible, updated_at=timezone.now())