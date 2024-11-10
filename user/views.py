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

class CreateUserView(APIView) :
    @swagger_auto_schema(tags=['유저를 생성합니다.'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'name': openapi.Schema(type=openapi.TYPE_STRING, description='유저 이름'),
            'affiliation': openapi.Schema(type=openapi.TYPE_STRING, description='소속'),
            'building': openapi.Schema(type=openapi.TYPE_STRING, description='건물'),
            'is_visible': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='가시성'),
        }
    ))
    # TODO: 학번 hash화
    def post(self, request):
        return HttpResponse('User Create')
    

class ProfileMeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [IsLoginUser]

#    @swagger_auto_schema(tags=['회원 프로필 조회'], request_body=None)
#    def get(self, request):
#        try:
#            # 현재 로그인한 사용자의 student_number를 가져옴
#            student_number = request.user.student_number
            
#            ## `authn_info`로 user 정보 가져오기
#            #user = users.objects.get(authn_info__student_number=student_number)
            
#            ## 사용자 데이터 직렬화
#            #user_info_serializer = UserAllInfoSerializer(user)
#            #user_data = user_info_serializer.data

#            user_serializer_data = self.find_one_user_serializer_by_student_number(student_number)
            
#            print("user_serializer_data: ", user_serializer_data)


#            # cabinet 정보 조회
#            cabinet_info = cabinets.objects.get(user_id=user_serializer_data['id'])
#            if not cabinet_info:
#                return Response({"error": "Cabinet not found for this user"}, status=status.HTTP_404_NOT_FOUND)
            
#            print("cabinet_info: ", cabinet_info)

#            # cabinet 데이터 직렬화
#            cabinet_info_serializer = CabinetAllInfoSerializer(cabinet_info)
#            cabinet_data = cabinet_info_serializer.data

#            print("cabinet_data: ", cabinet_data)

#            # cabinet_data가 직렬화된 데이터로서 dict 형태인 경우
#            building_id = cabinet_data['building_id']  # 단순히 ID 값만 가져옴
#            building = buildings.objects.get(id=building_id)  # buildings 모델에서 데이터 조회
            
#            # cabinet_history 정보 조회
#            cabinet_history_info = cabinet_histories.objects.filter(cabinet_id=cabinet_data['id']).first()
#            print("cabinet_history_info: ", cabinet_history_info)
#            if not cabinet_history_info:
#                return Response({"error": "Cabinet history not found"}, status=status.HTTP_404_NOT_FOUND)

#            # cabinet_history 정보 조회
#            cabinet_history_info = cabinet_histories.objects.filter(cabinet_id=cabinet_data['id']).first()

#            # cabinet_history_info가 실제 객체인지 확인합니다.
#            if cabinet_history_info is None:
#                return Response({"error": "Cabinet history not found"}, status=status.HTTP_404_NOT_FOUND)
            
#            # cabinet_history 데이터 직렬화
#            cabinet_history_serializer = CabinetHistoryAllInfoSerializer(cabinet_history_info)
#            cabinet_history_data = cabinet_history_serializer.data
#            print("cabinet_history_data: ", cabinet_history_data)
                        
#            # Calculate leftDate as the difference in days
#            expired_at = datetime.strptime(cabinet_history_data['expired_at'], "%Y-%m-%dT%H:%M:%SZ")
#            current_time = datetime.now()
#            left_date = (expired_at - current_time).days
            
#            # profile_data 구성 (snake_case)
#            profile_data = {
#                'name': user_serializer_data['name'],
#                'is_visible': user_serializer_data['is_visible'],
#                'affiliation': user_serializer_data['affiliation'],
#                'student_number': student_number,
#                'phone_number': user_serializer_data['phone_number'],
#                'rent_cabinet_info': {
#                    'building': building.name,  # buildings의 name 필드
#                    'floor': building.floor,  # buildings의 floor 필드
#                    'cabinet_number': cabinet_data['cabinet_number'],
#                    'status': cabinet_data['status'],
#                    'started_at': cabinet_history_data['created_at'],
#                    'expired_at': cabinet_history_data['expired_at'],
#                    'left_date': left_date,
#                }
#            }

#            #print("profile_data: ", profile_data)

#            ## 응답 직렬화 및 반환
#            profile_serializer = GetProfileMeDto(profile_data)
#            return Response(profile_serializer, status=status.HTTP_200_OK)
#        except users.DoesNotExist:
#            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
#        except authns.DoesNotExist:
#            return Response({'error': 'Authn record not found'}, status=status.HTTP_404_NOT_FOUND)
#        except Exception as e:
#            print(f"Unexpected error: {e}")
#            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    @swagger_auto_schema(
        tags=['회원 프로필 조회'],
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
        except users.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except authns.DoesNotExist:
            return Response({'error': 'Authn record not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Unexpected error: {e}")
            return Response({'error': 'Internal Server Error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    #@swagger_auto_schema(tags=['내 프로필을 수정합니다.'], request_body=openapi.Schema())
    def post(self, request):

        isVisible = request.data['isVisible']

        if isVisible == True:
            return HttpResponse('Update Visible True')
        else:
            return HttpResponse('Update Visible False')
    