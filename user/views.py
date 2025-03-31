import os
import sqlparse
import logging
from django.conf import settings
from django.core.management import call_command
from django.db import connection, transaction

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi

from core.middleware.authentication import IsLoginUser, IsAdminUser
from .serializers import GetProfileMeSerializer
from .models import users
from authn.models import authns
from cabinet.models import buildings


from user.serializer import (
    UserAdminCreateSerializer
)

from user.dto import (
    UserProfileUpdateDto
)

logger = logging.getLogger(__name__)

from user.business.user_service import UserService

user_service = UserService()


class UserProfileMeView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]
    
    @swagger_auto_schema(
        tags=['회원 본인 프로필 조회'],
        request_body=None,
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description='이름'),
                    'isVisible': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='이름 공개 여부'),
                    'affiliation': openapi.Schema(type=openapi.TYPE_STRING, description='소속'),
                    'studentNumber': openapi.Schema(type=openapi.TYPE_STRING, description='학번'),
                    'phoneNumber': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호'),
                    'rentCabinetInfo': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'building': openapi.Schema(type=openapi.TYPE_STRING, description='건물 이름'),
                            'floor': openapi.Schema(type=openapi.TYPE_INTEGER, description='층'),
                            'cabinetNumber': openapi.Schema(type=openapi.TYPE_INTEGER, description='캐비넷 번호'),
                            'status': openapi.Schema(type=openapi.TYPE_STRING, description='캐비넷 상태'),
                            'startDate': openapi.Schema(type=openapi.FORMAT_DATETIME, description='사용 시작일'),
                            'endDate': openapi.Schema(type=openapi.FORMAT_DATETIME, description='사용 종료일'),
                            'leftDate': openapi.Schema(type=openapi.TYPE_INTEGER, description='남은 일수'),
                        }
                    ),
                }
            ),
            401: "로그인 페이지로 이동",
            500: "컴포넌트들에 서버 통신 에러 문구 출력"
        }
    )
    def get(self, request):
            user = user_service.get_user_by_student_number(request.user.student_number)        
            
            serializer = GetProfileMeSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        tags=['회원 본인 프로필 수정'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'isVisible': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='이름 공개 여부'),
            }
        ),
        responses={
            200: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='User updated successfully'),
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='isVisible is required'),
                }
            ),
            404: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='User not found'),
                }
            ),
            500: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Internal Server Error'),
                }
            )
        }
    )
    def post(self, request):

        dto = UserProfileUpdateDto.create_validated(data=request.data)
        user_service.update_user_is_visible_by_student_number(student_number=request.user.student_number, is_visible=dto.validated_data['isVisible'])
        return Response({'message': 'User updated successfully'}, status=status.HTTP_200_OK)



class AdminUserCreateView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsAdminUser]

    @swagger_auto_schema(
        tags=['관리자 유저 생성'],
        request_body=UserAdminCreateSerializer,
        responses={
            201: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING, description='User created successfully'),
                }
            ),
            400: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='학번, 이름, 소속, 전화번호, isVisible 필수 입력값'),
                }
            ),
            500: openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING, description='Internal Server Error'),
                }
            )
        }
    )
    def post(self, request):

        create_user_dto = UserAdminCreateSerializer(data=request.data)

        if not create_user_dto.is_valid():
            return Response(create_user_dto.errors, status=status.HTTP_400_BAD_REQUEST)
        
        building_id = buildings.objects.get(name=create_user_dto.validated_data['buildingName'], 
                                            floor=create_user_dto.validated_data['floor'],
                                            section=create_user_dto.validated_data['section']).id
        
        if not building_id:
            return Response({'error': 'Building not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            users.objects.create(
                name=create_user_dto.validated_data['name'],
                affiliation=create_user_dto.validated_data['affiliation'],
                phone_number=create_user_dto.validated_data['phoneNumber'],
                building_id=building_id,
            )
        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({'error': 'User already exists'}, status=status.HTTP_409_CONFLICT)

        try :
            user_id = users.objects.filter(
                name=create_user_dto.validated_data['name'],
                affiliation=create_user_dto.validated_data['affiliation'],
                phone_number=create_user_dto.validated_data['phoneNumber'],
                building_id=building_id,
            ).first().id
            authns.objects.create(user_id=user_id ,student_number=create_user_dto.validated_data['studentNumber'],
                                  password=create_user_dto.validated_data['password'],
                                  role=create_user_dto.validated_data['role'])
        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({'error': 'Authn already exists'}, status=status.HTTP_409_BAD_REQUEST)
        
        return Response({'message': 'User created successfully'}, status=status.HTTP_201_CREATED)


class AdminUserDeleteView(APIView):
    pass
    


class MockupView(APIView):
    permission_classes = [AllowAny]  # WARNING: Allowing any user to execute this is insecure. Restrict permissions as needed.

    @swagger_auto_schema(
        tags=['데이터베이스 초기화'],
        request_body=None,
        responses={
            200: openapi.Response(
                description="Database flushed and SQL files executed successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Database flushed and SQL files executed successfully.'
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="SQL directory not found or SQL file missing.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='SQL directory not found or SQL file missing.'
                        )
                    }
                )
            ),
            500: openapi.Response(
                description="Internal Server Error.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Internal Server Error.'
                        )
                    }
                )
            ),
        }
    )
    def post(self, request):
        try:
            with transaction.atomic():
                # Flush the database, removing all data
                call_command('flush', '--noinput')
                logger.info("Database flushed successfully.")

                # Define the path to the SQL files
                sql_dir = os.path.join(settings.BASE_DIR, 'sql')  # Adjust the path as needed

                if not os.path.isdir(sql_dir):
                    error_msg = f"SQL directory not found at {sql_dir}."
                    logger.error(error_msg)
                    return Response({'error': error_msg}, status=status.HTTP_400_BAD_REQUEST)

                # Specify the ordered list of SQL files
                ordered_sql_files = [
                    'user_buildings.sql',
                    'user_users.sql',
                    'authn_authns.sql',
                    'cabinet_cabinets.sql',
                    'cabinet_cabinet_positions.sql',
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