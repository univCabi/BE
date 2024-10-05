from authn.authenticate import LoginAuthenticate
from authn.serializers import LoginSerializer
from .jwt import CustomLoginJwtToken
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi


class LoginView(APIView):
    ## Query Param EXAMPLE
    #@swagger_auto_schema(tags=['지정한 데이터의 상세 정보를 불러옵니다.'], query_serializer=TaskSearchSerializer, responses={200: 'Success'})
    #def get(self, request):
    #    return HttpResponse('User Login')
    
    permission_classes = [AllowAny]
    authentication_classes = [LoginAuthenticate]

    # Request Body EXAMPLE
    @swagger_auto_schema(tags=['로그인을 합니다.'], request_body=LoginSerializer)
    def post(self, request):

        #DB flushall
        #users.objects.all().delete()
        #authns.objects.all().delete()

        #users.objects.create(
        #    name = "민영재",
        #    affiliation = "전자정보통신공학부 전자공학전공",
        #    building = "누리관",
        #    visibility = True,
        #)

        # 테스트 용 DB 저장
        #authns.objects.create(
        #    user_id = userInfo,
        #    student_number = request.data.get("student_number"),
        #    password=make_password(request.data.get("password")),  # Hash the password
        #)

        user = request.user

        #print("user : ", user)

        if user is not None:
            # Generate JWT tokens (access and refresh)
            refresh = CustomLoginJwtToken.get_token(user)

            response = HttpResponse('User Login Success')

            response.set_cookie('access_token', str(refresh.access_token))
            response.set_cookie('refresh_token', str(refresh))

            return response
            
            # Return the tokens in the response
            #return Response({
            #    'access_token': str(refresh.access_token),
            #    'refresh_token': str(refresh),
            #})
        else:
            return Response({"error": "Invalid Credentials"}, status=400)



#class LoginView(APIView):
#    permission_classes = [AllowAny]



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['로그아웃을 합니다.'], request_body=LoginSerializer)
    def post(self, request):
        request.auth.delete()  # Delete the token to log out
        return Response({"message": "Logged out successfully"}, status=204)