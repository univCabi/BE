from django.http import HttpResponse

from rest_framework.views import APIView
from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi

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