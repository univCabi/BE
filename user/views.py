from django.http import HttpResponse

from rest_framework.views import APIView
from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi

from user.serializers import GetProfileMe, UpdateProfileMe

from rest_framework.permissions import IsAuthenticated, AllowAny
from authn.authenticate import IsLoginUser

from .models import users

from authn.models import authns

from cabinet.models import cabinets

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
            #student_number = request.user

            #user_id = authns.get_by_student_number(student_number)

            #print("USER ID", user_id)

            #user_info = users.find_one_userinfo_by_id(id=str(user_id))
            
            #print("USER", user_info)

            #GetProfileMe_serializer = GetProfileMe(user_info)

            #print("GET", GetProfileMe_serializer.data)

            user_profile_me_info = {
            'name': '민영재',
            'isVisible': True,
            'affiliation': '나노융합공학전공',
            'studentNumber': '202111741',
            'phoneNumber': '01012345678',
            'RentCabinetInfo': {
                'building': '공학관',
                'floor': '13',
                'cabinetNumber': '42',
                'status': 'USING',
                'startDate': '2024-09-01',
                'endDate': '2024-12-31',
                'leftDate': 42,
                }
            }

        # Return mock data as a response
            return Response(user_profile_me_info, status=status.HTTP_200_OK)




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
        return HttpResponse('Update Profile Me')