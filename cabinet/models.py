from django.db import models
from user.models import users

# Create your models here.
class cabinets(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.CASCADE, null=True)
    building = models.CharField(max_length=50)
    floor = models.CharField(max_length=50)
    number = models.CharField(max_length=50)
    payable = models.TextChoices('PAID', 'FREE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.building + self.floor + self.number

class cabinet_histories(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(users, on_delete=models.CASCADE, null=True)
    cabinet_id = models.ForeignKey(cabinets, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.cabinet_id + self.user_id + self.action