from django.http import HttpResponse
from django.views import View
from user.serializers import TaskSearchSerializer, TaskPostSerializer

from rest_framework.views import APIView
from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi


# Create your views here.

class LoginView(APIView):
    # Query Param EXAMPLE
    @swagger_auto_schema(tags=['지정한 데이터의 상세 정보를 불러옵니다.'], query_serializer=TaskSearchSerializer, responses={200: 'Success'})
    def get(self, request):
        return HttpResponse('User Login')
    
    # Request Body EXAMPLE
    @swagger_auto_schema(tags=['데이터를 생성합니다.'], request_body=TaskPostSerializer)
    def post(self, request):
        return HttpResponse('User Login')

class LogoutView(View):
    def get(self, request):
        return HttpResponse('User Logout')