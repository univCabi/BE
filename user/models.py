from django.db import models


""" 
users model
"""
class users(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    affiliation = models.CharField(max_length=50)
    phoneNumber = models.CharField(max_length=20)
    building = models.CharField(max_length=50)
    is_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.id

    @classmethod
    def find_one_userinfo_by_id(cls, id):
        return cls.objects.get(id=id)
    