from django.db import connection 
from core.middleware.authentication import LoginAuthenticate, IsLoginUser, IsValidRefreshToken
from authn.serializer import (
    AuthLoginSerializer
)
from core.middleware.jwt import CustomLoginJwtToken

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi
from user.models import users
from authn.models import authns

import os
import sqlparse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging

logger = logging.getLogger(__name__)


class LoginView(APIView):
    
    permission_classes = [AllowAny]
    authentication_classes = [LoginAuthenticate]

    @swagger_auto_schema(    
        tags=['회원 로그인 기능'], 
        request_body=AuthLoginSerializer, 
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'accessToken': openapi.Schema(type=openapi.TYPE_STRING, description='Access Token'),
                    'refreshToken': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh Token')
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Invalid Credentials')
                }
            ),
            401: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unauthorized')
                }
            )
        }
    )
    def post(self, request):
        user = request.user
        if request.user is not None:
            refresh = CustomLoginJwtToken.get_token(user)
            
            response = Response({
                'accessToken': str(refresh.access_token),
                # 'refreshToken': str(refresh)  # 응답 본문에 포함하지 않음
            }, status=status.HTTP_200_OK)
            

            response.set_cookie(
                key='refreshToken',
                value=str(refresh),
                samesite='Strict'      # CSRF 방지를 위해 설정    
            )
            return response
        else:
            return Response({"error": "Invalid Credentials"}, status=400)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]  # JWT 인증 클래스 추가

    @swagger_auto_schema(
        tags=['회원 로그아웃 기능'], 
        request_body=None,
        responses={
            200: openapi.Response(
                description="로그아웃 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING, description='Logout successful.')
                    })
            ),
            400: openapi.Response(
                description="로그아웃 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='No refresh token provided.')
                    })
            ),
            500: openapi.Response(
                description="로그아웃 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Logout failed.')
                    })
            )
        }
    )
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refreshToken')
            if refresh_token is None:
                return Response({"error": "No refresh token provided."}, status=status.HTTP_400_BAD_REQUEST)
            
            response = Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
            response.delete_cookie('refreshToken')  # 쿠키 삭제
            return response
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return Response({"error": "Logout failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CreateUserView(APIView):
    permission_classes = [AllowAny]
    #authentication_classes = []

    @swagger_auto_schema(tags=['회원가입을 합니다.'], request_body=AuthLoginSerializer, responses={
        200: openapi.Response(
            description="성공적으로 조회되었습니다.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='Database flushed and SQL files executed successfully.')
                })
        ),
        400: openapi.Response(
            description="SQL file not found.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='SQL file not found: {sql_file}')
                })
        ),
        404: openapi.Response(
            description="Building with the specified name and floor not found.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='SQL directory not found at {sql_dir}.')
                })
        ),
        500: openapi.Response(
            description="Unexpected error executing SQL files.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Error executing SQL files: {e}')
                })
        )
        })
    def post(self, request):
        try:
                # Define the path to the SQL files
                sql_dir = os.path.join(settings.BASE_DIR, 'sql')  # Adjust the path as needed

                if not os.path.isdir(sql_dir):
                    error_msg = f"SQL directory not found at {sql_dir}."
                    logger.error(error_msg)
                    return Response({'error': error_msg}, status=status.HTTP_404_NOT_FOUND)

                # Specify the ordered list of SQL files
                ordered_sql_files = [
                    'playable.sql'
                ]

                # Execute each SQL file in the specified order
                with connection.cursor() as cursor:
                    for sql_file in ordered_sql_files:
                        print("executed")
                        sql_path = os.path.join(sql_dir, sql_file)
                        if not os.path.isfile(sql_path):
                            error_msg = f"SQL file not found: {sql_file}"
                            logger.error(error_msg)
                            return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)
                        
                        with open(sql_path, 'r', encoding='utf-8') as file:
                            sql_content = file.read()
                            # Use sqlparse to split the SQL content into individual statements
                            statements = sqlparse.split(sql_content)
                            
                            for statement in statements:
                                statement = statement.strip()
                                print(statement)
                                if statement:  # Avoid executing empty statements
                                    try:
                                        cursor.execute(statement)
                                        #logger.info(f"Executed statement from {sql_file}: {statement[:50]}...")  # Log first 50 chars
                                    except Exception as exec_err:
                                        logger.error(f"Error executing statement from {sql_file}: {exec_err}")
                                        raise exec_err  # This will trigger a rollback
                                
                return Response({'message': 'Database flushed and SQL files executed successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error executing SQL files: {e}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteUserView(APIView):
    permission_classes = [AllowAny]
    #authentication_classes = []

    @swagger_auto_schema(tags=['회원탈퇴를 합니다.'], responses={
        204: openapi.Response(
            description="성공적으로 삭제되었습니다.",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='User deleted successfully.')
                })
        )
        })
    def post(self, request):
        user_ids = [2501, 2502, 2503]

        # authns 테이블에서 삭제
        authns.objects.filter(user_id__in=user_ids).delete()

        # users 테이블에서 삭제
        users.objects.filter(id__in=user_ids).delete()

        print(f"Deleted users and authns entries for user_ids: {user_ids}")
        return Response({"message": "User deleted successfully"}, status=204)

class ReIssueAccessTokenView(APIView):
    authentication_classes = [IsValidRefreshToken]  # 필요 시 활성화

    @swagger_auto_schema(
        tags=['Access Token 재발급'],
        request_body=None,
        responses={
            200: openapi.Response(
                description="Access Token 재발급 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'accessToken': openapi.Schema(type=openapi.TYPE_STRING, description='Access Token')
                    })
            ),
            401: openapi.Response(
                description="Access Token 재발급 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(type=openapi.TYPE_STRING, description='Unexpected error')
                    })
            )
        }
    )
    def post(self, request):
        try:
            response = Response({
                'accessToken': str(request.auth.access_token),
                # 'refreshToken': str(refresh)  # 응답 본문에 포함하지 않음
            }, status=status.HTTP_200_OK)
            
            return response

        except Exception as e:
            logger.error(f"Unexpected error in AccessTokenView: {str(e)}")
            return Response({"error": "Unexpected error"}, status=status.HTTP_401_UNAUTHORIZED)
        