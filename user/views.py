from django.http import HttpResponse
from rest_framework.views import APIView
from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi
from rest_framework.permissions import IsAuthenticated, AllowAny
from authn.authenticate import IsLoginUser

from user.dto import GetProfileMeDto, UpdateProfileMeDto
from .models import users
from authn.models import authns


from rest_framework.response import Response
from rest_framework import status


class ProfileMeView(APIView):
    permission_classes = [AllowAny]
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
        try:
            # Get the currently logged-in user's student number
            student_number = request.user.student_number
            
            # Get user instance by student number
            user = users.find_one_userinfo_by_student_number(student_number=student_number)
            
            # Serialize the user with GetProfileMeDto
            profile_serializer = GetProfileMeDto(user)
            return Response(profile_serializer.data, status=status.HTTP_200_OK)
        
        except users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except authns.DoesNotExist:
            return Response({'error': 'Authn record not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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
        student_number = request.user.student_number
        
        is_visible = request.data.get('isVisible')

        if is_visible is None:
            return Response({'error': 'isVisible is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            users.update_user_is_visible_by_student_number(student_number=student_number, is_visible=is_visible)
            return Response({'message': 'User updated successfully'}, status=status.HTTP_200_OK)
        except users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    