from authn.models import authns
from rest_framework import authentication
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication, JWTStatelessUserAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import check_password
import jwt
from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError

from .utils import decrypt_student_number
import logging

logger = logging.getLogger(__name__)

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
    
class IsValidRefreshToken(JWTStatelessUserAuthentication):
    def authenticate(self, request):
        refresh_token = request.COOKIES.get('refreshToken')

        if not refresh_token:
            logger.warning("Refresh token not provided.")
            raise AuthenticationFailed('Authentication credentials were not provided.', code='authentication_credentials_not_provided')

        # RefreshToken 객체 생성 시 예외 발생 가능
        try:
            refresh = RefreshToken(refresh_token)
            return (None, refresh)  # (user, auth)에서 user는 None
        except TokenError as e:
            logger.error(f"Token error: {str(e)}")
            raise AuthenticationFailed(
                detail={
                    'error': 'Given token not valid for any token type',
                    'messages': [
                        {'token_class': 'RefreshToken', 'token_type': 'refresh', 'message': 'Token is invalid or expired'}
                    ]
                },
                code='token_not_valid'
            )
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired.")
            raise AuthenticationFailed(
                detail={
                    'error': 'Given token not valid for any token type',
                    'messages': [
                        {'token_class': 'RefreshToken', 'token_type': 'refresh', 'message': 'Token is invalid or expired'}
                    ]
                },
                code='token_not_valid'
            )
        except jwt.InvalidTokenError:
            logger.error("Invalid refresh token.")
            raise AuthenticationFailed(
                detail={
                    'error': 'Given token not valid for any token type',
                    'messages': [
                        {'token_class': 'RefreshToken', 'token_type': 'refresh', 'message': 'Token is invalid or expired'}
                    ]
                },
                code='token_not_valid'
            )
        except Exception as e:
            logger.error(f"Unexpected error during RefreshToken creation: {str(e)}")
            raise AuthenticationFailed(
                detail={
                    'error': 'Given token not valid for any token type',
                    'messages': [
                        {'token_class': 'RefreshToken', 'token_type': 'refresh', 'message': 'Token is invalid or expired'}
                    ]
                },
                code='token_not_valid'
            )

class IsLoginUser(JWTAuthentication):
    def get_user(self, validated_token):
        if 'student_number' not in validated_token:
            logger.error("Token contained no student_number.")
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")
        
        student_number = validated_token.get('student_number')
        if student_number is None:
            logger.error("student_number is None in token.")
            raise AuthenticationFailed(_("Token contained no recognizable user identification"), code="token_not_valid")
        
        # student_number 복호화
        try:
            decoded_student_number = decrypt_student_number(student_number)
            logger.debug(f"Decoded student_number: {decoded_student_number}")
        except Exception as e:
            logger.error(f"Failed to decrypt student number: {str(e)}")
            raise AuthenticationFailed(_("Failed to decrypt student number."), code="token_decryption_failed")
        
        # 사용자 조회
        try:
            user = authns.objects.get(student_number=decoded_student_number)
            if not user.is_active:
                logger.warning(f"User {user} is inactive.")
                raise AuthenticationFailed(_("User is inactive"), code="user_inactive")
            return user
        except authns.DoesNotExist:
            logger.warning(f"User with student_number {decoded_student_number} not found.")
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

class IsAdminUser(IsLoginUser):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if user.role != 'ADMIN':
            logger.warning(f"User {user} is not an admin.")
            raise AuthenticationFailed(_("User is not an admin"), code="user_not_admin")
        return user