from django.utils import timezone
from django.db import models
from user.models import users, buildings

from cabinet.type import (CabinetStatusEnum,
                          CabinetPayableEnum)

#TODO: 반납기한에 대한 로직 추가


# Create your models here.
class cabinets(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.SET_NULL, null=True)
    building_id = models.ForeignKey(buildings, on_delete=models.SET_NULL, null=True)
    cabinet_number = models.IntegerField()
    status = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in CabinetStatusEnum], default='AVAILABLE')
    payable = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in CabinetPayableEnum], default='FREE')
    reason = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.building_id)
    
    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    @classmethod
    def find_one_rented_cabinet_by_cabinet_id(cls, cabinet_id) :
        return cls.objects.get(id=cabinet_id)
    

class cabinet_histories(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.CASCADE)
    cabinet_id = models.ForeignKey(cabinets, models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField(null=False)
    updated_at = models.DateTimeField(auto_now=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return str(self.cabinet_id)
    
    @classmethod
    def find_all_cabinet_by_user_id(cls, user_id):
        return cls.objects.filter(user_id=user_id)

    @classmethod
    def create_rent_cabinet_history(cls, user_id, cabinet_id, expired_at, status):
        return cls.objects.create(user_id=user_id, cabinet_id=cabinet_id, expired_at=expired_at).update(status='USING')
    
    @classmethod
    def create_return_cabinet_history(cls, user_id, cabinet_id):
    # ended_at이 None인 기존 이력이 있는지 확인하고 업데이트
        return cls.objects.filter(user_id=user_id, cabinet_id=cabinet_id, ended_at=None).update(ended_at=timezone.now(), status='AVAILABLE')

    
class cabinet_positions(models.Model) :
    cabinet_id = models.OneToOneField(cabinets, on_delete=models.CASCADE)
    cabinet_x_pos = models.IntegerField()
    cabinet_y_pos = models.IntegerField()


    def __str__(self):
        return str(self.cabinet_id)