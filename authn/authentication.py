from authn.models import authns
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password

from .utils import decrypt_student_number

class LoginAuthenticate(authentication.BaseAuthentication):
    def authenticate(self, request):
        student_number = request.data.get('studentNumber')
        password = request.data.get('password')

        if not student_number or not password:
            return None

        try:
            authn_info = authns.objects.get(student_number=student_number)
        except authns.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')

        # Verify the password using Django's check_password function
        if not check_password(password, authn_info.password):
            raise exceptions.AuthenticationFailed('Incorrect password')

        return (authn_info, None)
    
class IsLoginUser(JWTAuthentication):
    def get_user(self, validated_token):
        if 'student_number' not in validated_token:
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")
        student_number = validated_token.get('student_number')  # `student_number` 사용
        if student_number is None:
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")

        # 사용자 조회
        try:
            decoded_student_number = decrypt_student_number(student_number)
            user = authns.objects.get(student_number=decoded_student_number)
        except authns.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")
    
        #if user.role == 'ADMIN':
        #    raise AuthenticationFailed(_("User is not an admin"), code="user_not_admin")

        return user
    
class IsAdminUser(JWTAuthentication):
    def get_user(self, validated_token):
        if 'student_number' not in validated_token:
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")
        student_number = validated_token.get('student_number')  # `student_number` 사용
        if student_number is None:
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")

        # 사용자 조회
        try:
            decoded_student_number = decrypt_student_number(student_number)
            user = authns.objects.get(student_number=decoded_student_number)
        except authns.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        if user.role == 'NORMAL':
            raise AuthenticationFailed(_("User is not an admin"), code="user_not_admin")

        return user