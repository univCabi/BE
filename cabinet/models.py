from django.db import models
from user.models import users
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

class CabinetStatusEnum(Enum):
    BROKEN = 'BROKEN'
    AVAILABLE = 'AVAILABLE'
    USING = 'USING'
    OVERDUE = 'OVERDUE'

class CabinetPayableEnum(Enum):
    PAID = 'PAID'
    FREE = 'FREE'

class buildings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, choices=[(tag, tag.value) for tag in BuildingNameEnum])
    floor = models.CharField(max_length=10)
    width = models.IntegerField()
    height = models.IntegerField()

    def __str__(self):
        return self.name

# Create your models here.
class cabinets(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.CASCADE, null=True)
    building_id = models.OneToOneField(buildings, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[(tag, tag.value) for tag in CabinetStatusEnum], default='AVAILABLE')
    payable = models.CharField(max_length=20, choices=[(tag, tag.value) for tag in CabinetPayableEnum], default='FREE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.building_id + self.status + self.payable
    

class cabinet_histories(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.OneToOneField(users, on_delete=models.CASCADE, null=True)
    cabinet_id = models.OneToOneField(cabinets, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cabinet_id + self.user_id + self.action
    
class cabinet_positions(models.Model) :
    cabinet_id = models.OneToOneField(cabinets, on_delete=models.CASCADE)
    cabinet_x_pos = models.IntegerField()
    cabinet_y_pos = models.IntegerField()
    cabinet_number = models.IntegerField()

    def __str__(self):
        return self.cabinet_id + self.cabinet_x_pos + self.cabinet_y_pos + self.cabinet_number
