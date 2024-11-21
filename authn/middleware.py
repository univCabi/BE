# jwt_refresh_middleware.py

from django.conf import settings
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
import jwt
from .utils import decrypt_student_number  # decrypt_student_number 함수 임포트
import logging
from authn.models import authns

logger = logging.getLogger(__name__)

class JWTRefreshMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_paths = getattr(settings, 'JWT_MIDDLEWARE_EXCLUDED_PATHS', [])

    def __call__(self, request):
        # 요청을 처리하기 전에 미들웨어 로직 실행
        response = self.process_request(request)
        if response:
            return response

        # 요청을 view로 전달
        response = self.get_response(request)

        # 응답을 처리하기 전에 미들웨어 로직 실행
        response = self.process_response(request, response)
        return response

    def process_request(self, request):
        # 제외 경로에 해당하면 미들웨어 로직을 건너뜀
        if any(request.path.startswith(path) for path in self.excluded_paths):
            logger.debug(f"Excluded path: {request.path}")
            return None

        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            access_token = auth_header.split(' ')[1]
            try:
                payload = jwt.decode(
                    access_token,
                    settings.SECRET_KEY,
                    algorithms=['HS256'],
                    options={'verify_exp': True}
                )
                encrypted_student_number = payload.get('student_number')
                if not encrypted_student_number:
                    logger.warning("student_number not found in token payload.")
                    return JsonResponse({'detail': 'Invalid token payload.'}, status=401)

                # student_number 복호화
                try:
                    decrypted_student_number = decrypt_student_number(encrypted_student_number)
                    logger.debug(f"Decrypted student_number: {decrypted_student_number}")
                except Exception as e:
                    logger.error(f"Failed to decrypt student number: {str(e)}")
                    return JsonResponse({'detail': 'Failed to decrypt student number.'}, status=401)

                # 사용자 조회
                try:
                    user = authns.objects.get(student_number=decrypted_student_number)
                    request.user = user
                    logger.debug(f"Authenticated user: {user}")
                except Exception as e:
                    logger.warning(f"User with student_number {decrypted_student_number} not found.")
                    return JsonResponse({'detail': 'User not found.'}, status=404)

            except jwt.ExpiredSignatureError:
                logger.info("Access token expired. Attempting to refresh.")
                # Access token 만료, Refresh token 확인
                refresh_token = request.COOKIES.get('refreshToken')
                if not refresh_token:
                    logger.warning("Refresh token not provided.")
                    return JsonResponse({'detail': 'Authentication credentials were not provided.'}, status=401)
                try:
                    refresh = RefreshToken(refresh_token)
                    new_access_token = str(refresh.access_token)
                    request.META['HTTP_AUTHORIZATION'] = f'Bearer {new_access_token}'
                    logger.info("Refresh token is valid. New access token issued.")

                    payload = jwt.decode(
                        new_access_token,
                        settings.SECRET_KEY,
                        algorithms=['HS256'],
                        options={'verify_exp': True}
                    )
                    encrypted_student_number = payload.get('student_number')
                    if not encrypted_student_number:
                        logger.warning("student_number not found in new token payload.")
                        return JsonResponse({'detail': 'Invalid token payload.'}, status=401)

                    # student_number 복호화
                    try:
                        decrypted_student_number = decrypt_student_number(encrypted_student_number)
                        logger.debug(f"Decrypted student_number: {decrypted_student_number}")
                    except Exception as e:
                        logger.error(f"Failed to decrypt student number: {str(e)}")
                        return JsonResponse({'detail': 'Failed to decrypt student number.'}, status=401)

                    # 사용자 조회
                    try:
                        user = authns.objects.get(student_number=decrypted_student_number)
                        logger.debug(f"Authenticated user with refreshed token: {user}")
                        request.user = user
                        request.new_access_token = new_access_token
                    except Exception as e:
                        logger.warning(f"User with student_number {decrypted_student_number} not found.")
                        return JsonResponse({'detail': 'User not found.'}, status=401)

                except (TokenError, InvalidToken) as e:
                    logger.error(f"Invalid refresh token: {str(e)}")
                    request.delete_refresh_cookie = True
                    return JsonResponse({'detail': 'Invalid refresh token. Please log in again.'}, status=401)
            except (jwt.InvalidTokenError, Exception) as e:
                logger.error(f"Invalid token: {str(e)}")
                return JsonResponse({'detail': 'Invalid token.'}, status=401)

    def process_response(self, request, response):
        if hasattr(request, 'new_access_token'):
            response['Authorization'] = f'Bearer {request.new_access_token}'
            logger.debug("New access token added to response headers.")
        if hasattr(request, 'delete_refresh_cookie') and request.delete_refresh_cookie:
            response.delete_cookie('refreshToken')
            logger.debug("Refresh token cookie deleted from response.")
        return response
