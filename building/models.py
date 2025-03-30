from django.db import models
from building.type.BuildingNameEnum import BuildingNameEnum

# Create your models here.
class buildings(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, choices=[(tag.value, tag.value) for tag in BuildingNameEnum])
    floor = models.IntegerField()
    section = models.CharField(max_length=10)
    width = models.IntegerField()
    height = models.IntegerField()

    def __str__(self):
        return self.name