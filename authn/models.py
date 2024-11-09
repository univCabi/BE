from django.db import models
from enum import Enum
from user.models import users
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class RoleEnum(Enum):
    NORMAL = 'NORMAL'
    ADMIN = 'ADMIN'


""" 
authns model
"""
class AuthnsManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)  # This will hash the password
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        
        return self.create_user(email, password, **extra_fields)
    

class authns(AbstractBaseUser):
    user_id = models.OneToOneField(users, on_delete=models.CASCADE, related_name='user_info')
    student_number = models.CharField(max_length=50)
    password = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=[(tag, tag.value) for tag in RoleEnum], default='NORMAL')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    last_login = None

    objects = AuthnsManager()  # Link the custom manager

    USERNAME_FIELD = 'student_number'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.student_number
    
    @classmethod
    def get_by_student_number(cls, student_number):
        auth_instance = cls.objects.get(student_number=student_number)
        return auth_instance.id  # Return the related user_id