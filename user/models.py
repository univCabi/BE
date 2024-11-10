from django.db import models
from enum import Enum

class BuildingNameEnum(Enum):
    가온관 = '가온관'
    공학1관 = '공학1관'
    공학2관 = '공학2관'
    디자인관 = '디자인관'
    나래관 = '나래관'
    누리관 = '누리관'
    수산과학관 = '수산과학관'
    웅비관 = '웅비관'
    인문사회경영관 = '인문사회경영관'
    자연과학1관 = '자연과학1관'
    자연과학2관 = '자연과학2관'
    장영실관 = '장영실관'
    창의관 = '창의관'
    충무관 = '충무관'
    향파관 = '향파관'
    환경해양관 = '환경해양관'
    호연관 = '호연관'

""" 
users model
"""

class buildings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in BuildingNameEnum])
    floor = models.IntegerField()
    section = models.CharField(max_length=10)
    width = models.IntegerField()
    height = models.IntegerField()

    def __str__(self):
        return self.name
    
class users(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    affiliation = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    building_id = models.ForeignKey(buildings, on_delete=models.CASCADE, related_name='users')
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
        user = cls.objects.get(authn_info__student_number=student_number)
        user.is_visible = is_visible
        return user.save()