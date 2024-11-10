from authn.authenticate import LoginAuthenticate, IsLoginUser, IsAdminUser
from authn.serializers import LoginSerializer
from .jwt import CustomLoginJwtToken
from django.http import HttpResponse

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.hashers import make_password

from drf_yasg.utils       import swagger_auto_schema
from drf_yasg             import openapi
from user.models import users, buildings
from authn.models import authns


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

        user = request.user
        if request.user is not None:
            # GenerFernet.generate_key().decode()ate JWT tokens (access and refresh)
            refresh = CustomLoginJwtToken.get_token(user)

            response = HttpResponse('User Login Success')

            response.set_cookie('accessToken', str(refresh.access_token))
            response.set_cookie('refreshToken', str(refresh))

            #return response
        
            return Response({ 'accessToken': str(refresh.access_token), 'refreshToken': str(refresh) })
            
            
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
    authentication_classes = [IsLoginUser]  # JWT 인증 클래스 추가

    @swagger_auto_schema(tags=['로그아웃을 합니다.'], request_body=LoginSerializer)
    def post(self, request):
        response = Response({"message": "Logged out successfully"}, status=205)
        
        # 쿠키에서 토큰을 삭제하기 위해 빈 값을 설정하고, 즉시 만료
        response.delete_cookie('accessToken')
        response.delete_cookie('refreshToken')

        return response
        
from cabinet.models import cabinets, cabinet_histories, cabinet_positions

class CreateUserView(APIView):
    permission_classes = [AllowAny]
    #authentication_classes = []

    @swagger_auto_schema(tags=['회원가입을 합니다.'], request_body=LoginSerializer)
    def post(self, request):
        # Create a new user or update if already exists

        buildings.objects.update_or_create(
            name="가온관",
            floor = 1,
            section = "A",
            width = 1000,
            height = 1000,
        )

        building_info = buildings.objects.get(name="가온관", floor=1, section="A")
        
        print("building_info : ", building_info)
        id, created = users.objects.update_or_create(
            name="민영재",
            affiliation="전자정보통신공학부 전자공학전공",
            building_id=building_info,
            phone_number="010-1234-5678",
            is_visible=True,
        )

        #print("user : ", id)

        # Create or update the authns entry, ensure password is hashed
        authns_obj, created = authns.objects.update_or_create(
            user_id=id,  # Pass the full user instance here
            student_number='202111741',
            password=make_password("202111741"),  # Hash the password
            role='NORMAL'
        )

        # Manually set the password and save
        authns_obj.set_password("202111741")  # Hashes the password
        authns_obj.save()


        cabinet_id = cabinets.objects.create(
            user_id=id,
            building_id=building_info,
            cabinet_number=1,
            status='USING',
            payable='FREE'
        )
        
        cabinet_histories.objects.create(
            user_id=id,
            cabinet_id=cabinet_id,
            expired_at='2021-12-31 23:59:59'
        )

        cabinet_positions.objects.create(
            cabinet_id=cabinet_id,
            cabinet_x_pos=0,
            cabinet_y_pos=1000
        )



        return Response({"message": "User and authns created successfully"}, status=201)



class DeleteUserView(APIView):
    permission_classes = [AllowAny]
    #authentication_classes = []

    @swagger_auto_schema(tags=['회원탈퇴를 합니다.'], request_body=LoginSerializer)
    def post(self, request):
        users.objects.all().delete()
        authns.objects.all().delete()
        buildings.objects.all().delete()
        cabinets.objects.all().delete()
        cabinet_histories.objects.all().delete()
        cabinet_positions.objects.all().delete()
        return Response({"message": "User deleted successfully"}, status=204)
