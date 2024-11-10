from django.http import HttpResponse

from rest_framework.views import APIView
from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi

from user.serializers import GetProfileMeSerializer, UpdateProfileMeSerializer
from user.dto import GetProfileMeDto, UpdateProfileMeDto


from rest_framework.permissions import IsAuthenticated, AllowAny
from authn.authenticate import IsLoginUser

from .models import users

from authn.models import authns

from cabinet.models import cabinets

from rest_framework.response import Response
from rest_framework import status
from .serializers import UserAllInfoSerializer

from cabinet.serializers import CabinetAllInfoSerializer

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
    

class ProfileMeView(APIView) :
    permission_classes = [AllowAny]
    authentication_classes = [IsLoginUser]

    #@swagger_auto_schema(tags=['내 프로필을 불러옵니다.'], query_serializer=openapi.Schema(
    #    type=openapi.TYPE_OBJECT,
    #    properties={
    #        'name': openapi.Schema(type=openapi.TYPE_STRING, description='유저 이름'),
    #        'isVisible': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='가시성'),
    #        'affiliation': openapi.Schema(type=openapi.TYPE_STRING, description='소속'),
    #        'studentNumber': openapi.Schema(type=openapi.TYPE_STRING, description='학번'),
    #        'phoneNumber': openapi.Schema(type=openapi.TYPE_STRING, description='전화번호'),
    #        'RentCabinetInfo': openapi.Schema(
    #            type=openapi.TYPE_OBJECT,
    #            properties={
    #                'building': openapi.Schema(type=openapi.TYPE_STRING, description='건물'),
    #                'floor': openapi.Schema(type=openapi.TYPE_STRING, description='층'),
    #                'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING, description='캐비넷 번호'),
    #                'status': openapi.Schema(type=openapi.TYPE_STRING, description='상태'),
    #                'startDate': openapi.Schema(type=openapi.TYPE_STRING, description='사용 시작일'),
    #                'endDate': openapi.Schema(type=openapi.TYPE_STRING, description='사용 종료일'),
    #                'leftDate': openapi.Schema(type=openapi.TYPE_INTEGER, description='남은 일수'),
    #            }
    #        )
    #    }
    #))
    def get(self, request):
        #try:
            student_number = request.user

            user_id = authns.get_by_student_number(student_number)

            print("USER ID", user_id)

            print("User ID Type", type(user_id))

            #user_info = users.find_one_userinfo_by_id(id=user_id)
            # 특정 id로 데이터 조회
            user_info = users.objects.get(id=user_id)
            
            print("USER", user_info)
            # 데이터를 직렬화
            userInfoSerializer = UserAllInfoSerializer(user_info)
            user_data = userInfoSerializer.data

            print("USER DATA", user_data)

                # cabinet 정보 조회 및 직렬화
            #try:
            cabinet_info = cabinets.objects.get(user_id=user_id)
            print("CABINET INFO", cabinet_info)
            cabinet_info_serializer = CabinetAllInfoSerializer(cabinet_info)
            cabinet_data = cabinet_info_serializer.data
            print("CABINET DATA", cabinet_data)
            #except cabinets.DoesNotExist:
            #    cabinet_data = None  # 또는 {'message': 'No cabinet found for this user'}

            
            

            # 응답 데이터 구성
            profile_data = {
                'name': user_data['name'],
                'isVisible': user_data['is_visible'],
                'affiliation': user_data['affiliation'],
                'studentNumber': student_number,
                'phoneNumber': user_data['phone_number'],
                'RentCabinetInfo': {
                    'building': cabinet_data['building'],
                    
                }
            }

            # 응답 직렬화 및 반환
            profile_serializer = GetProfileMeDto(profile_data)
            return Response(profile_serializer.data, status=status.HTTP_200_OK)
        
            #except users.DoesNotExist:
            #    return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        # Return mock data as a response
            return Response(user_profile_me_info, status=status.HTTP_200_OK)
    
            #user_profile_me_info = {
            #'name': '민영재',
            #'isVisible': True,
            #'affiliation': '나노융합공학전공',
            #'studentNumber': 202111741,
            #'phoneNumber': '010-1234-5678',
            #'RentCabinetInfo': {
            #    'building': '공학관',
            #    'floor': 13,
            #    'cabinetNumber': 42,
            #    'status': 'USING',
            #    'startDate': '2024-09-01',
            #    'endDate': '2024-12-31',
            #    'leftDate': 42,
            #    }
            #}





        #except users.DoesNotExist:
        #    return HttpResponse('User not found', status=401)

        ## Serialize the user information
        #userSerializer = GetProfileMe(userInfo)
        ## Fetch the cabinet information associated with the user
        #try:
        #    cabinetInfo = cabinets.objects.get(user_id=userInfo.id)
        #except cabinets.DoesNotExist:
        #    return HttpResponse('Cabinet not found', status=401)

        ## Prepare the response data
        #response_data = {
        #    'user': userSerializer.data,
        #    'cabinet': {
        #        'building': cabinetInfo.building,
        #        'floor': cabinetInfo.floor,
        #        'cabinetNumber': cabinetInfo.cabinet_number,
        #        'status': cabinetInfo.status,
        #        'startDate': cabinetInfo.start_date,
        #        'endDate': cabinetInfo.end_date,
        #        'leftDate': (cabinetInfo.end_date - datetime.date.today()).days,
        #    }
        #}

        #return JsonResponse(response_data)
    
    #@swagger_auto_schema(tags=['내 프로필을 수정합니다.'], request_body=openapi.Schema())
    def post(self, request):

        isVisible = request.data['isVisible']

        if isVisible == True:
            return HttpResponse('Update Visible True')
        else:
            return HttpResponse('Update Visible False')