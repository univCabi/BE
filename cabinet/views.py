from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from authn.authentication import IsLoginUser
from drf_yasg import openapi

from rest_framework.response import Response
from rest_framework import status

from .serializers import requestFindAllCabinetInfoByBuildingNameAndFloor, lentCabinetByUserIdAndCabinetId, returnCabinetByUserIdAndCabinetId, searchCabinetAndBuildingByKeyWord, findAllCabinetHistoryByUserId, cabinetInfoSerializer, floorInfoItemSerializer, floorInfoSerializer, responseFindAllCabinetInfoByBuildingNameAndFloor
from .models import cabinets, buildings, cabinet_positions, cabinet_histories
from authn.models import authns

from user.models import users

from drf_yasg.utils import swagger_auto_schema

from .serializers import CabinetLogDto




# Create your views here.

class CabinetMainView(APIView):
    @swagger_auto_schema(tags=['특정건물과 특정층의 사물함 정보를 반환합니다.'], query_serializer=requestFindAllCabinetInfoByBuildingNameAndFloor, responses={200: 'Success'})
    def get(self, request):
        # 쿼리 파라미터로 건물명과 층수 받기
        serializer = requestFindAllCabinetInfoByBuildingNameAndFloor(data=request.query_params)
        
        # 입력값 유효성 검사
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        building_name = serializer.validated_data.get("buildingName")
        floor = serializer.validated_data.get("floor")
        
        # 해당 건물명과 층수를 가진 빌딩을 필터링
        try:
            building = buildings.objects.get(name=building_name, floor=floor)
        except buildings.DoesNotExist:
            return Response({"error": "Building not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # 해당 빌딩에 연결된 모든 사물함 조회
        cabinets_in_building = cabinets.objects.filter(building_id=building)

        # 반환해야 할 내용
        #cabinet_id
        #username -> nullable
        #is_visible -> nullable
        #is_mine -> boolean
        #x_pos
        #y_pos
        #cabinet_number
        #status
        #payable

        #cabinetInfo = [{}]
        #floorInfo = {floor width, height }
        
        for cabinet in cabinets_in_building :
            cabinets_positions = cabinet_positions.objects.filter(cabinet_id=cabinet.id)
            # 필요한 정보만 직렬화하여 반환
            data = [
                {
                    "id": cabinet.id,
                    "username": cabinet.user_id.id if cabinet.user_id else None,
                    "isVisible": cabinet.user_id.is_visible if cabinet.user_id else None,
                    "isMine": True if cabinet.user_id == request.user else False,
                    "xPos": cabinet_positions.cabinet_x_pos,
                    "yPos": cabinet_positions.cabinet_y_pos,
                    "cabinetNumber": cabinet_positions.cabinet_number,
                    "status": cabinet.status,
                    "payable": cabinet.payable
                }
                
            ]
        

        return Response(data, status=status.HTTP_200_OK)
        
#최대 6개    
class CabinetSearchView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'result': request.GET.get('keyword')})
    

# 당장은 모두 받기
# 나중에 무한 스크롤
class CabinetRentView(APIView):

    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(tags=['사물함을 대여합니다.'], request_body=lentCabinetByUserIdAndCabinetId)
    def post(self, request):
        # 유저 ID와 사물함 ID 받기
        serializer = lentCabinetByUserIdAndCabinetId(data=request.data)
    
        # 입력값 유효성 검사
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response.status(status.HTTP_200_OK)

class CabinetReturnView(APIView):

    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response.status(status.HTTP_200_OK)


class CabinetSearchDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        cabinetSearchResult = [
            {
                "building": "가온관",
                "floor": 2,
                "cabinetNumber": 1,
            },
            {
                "building": "건축관",
                "floor": 2,
                "cabinetNumber": 2,
            },
            {
                "building": "공학1관",
                "floor": 3,
                "cabinetNumber": 2,
            },
            {
                "building": "공학2관",
                "floor": 2,
                "cabinetNumber": 3,
            }
        ]

        return Response(cabinetSearchResult, status=status.HTTP_200_OK)
    

class CabinetFloorView(APIView) :
    permission_classes = [AllowAny]
    def get(self, request):
        building_name = request.GET.get('building')
        floor = request.GET.get('floor')


        floorInfo = {
                "request_building": building_name,
                "requet_floor": floor,
                "floor": 1,
                "floorWidth": 500,
                "floorHeight": 1000,
                "cabinets": [
                    {
                        "cabinetNumber": 1,
                        "xPos": 0,
                        "yPos": 1000,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 2,
                        "xPos": 0,
                        "yPos": 900,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 3,
                        "xPos": 0,
                        "yPos": 800,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 4,
                        "xPos": 0,
                        "yPos": 700,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 5,
                        "xPos": 0,
                        "yPos": 600,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 6,
                        "xPos": 0,
                        "yPos": 500,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 7,
                        "xPos": 0,
                        "yPos": 400,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 8,
                        "xPos": 0,
                        "yPos": 300,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 9,
                        "xPos": 0,
                        "yPos": 200,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 10,
                        "xPos": 0,
                        "yPos": 100,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 11,
                        "xPos": 100,
                        "yPos": 1000,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 12,
                        "xPos": 100,
                        "yPos": 900,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 13,
                        "xPos": 100,
                        "yPos": 800,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 14,
                        "xPos": 100,
                        "yPos": 700,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 15,
                        "xPos": 100,
                        "yPos": 600,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 16,
                        "xPos": 100,
                        "yPos": 500,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 17,
                        "xPos": 100,
                        "yPos": 400,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 18,
                        "xPos": 100,
                        "yPos": 300,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 19,
                        "xPos": 100,
                        "yPos": 200,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 20,
                        "xPos": 100,
                        "yPos": 100,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 21,
                        "xPos": 200,
                        "yPos": 1000,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 22,
                        "xPos": 200,
                        "yPos": 900,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 23,
                        "xPos": 200,
                        "yPos": 800,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 24,
                        "xPos": 200,
                        "yPos": 700,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber" : 25,
                        "xPos": 200,
                        "yPos": 600,
                        "status": "BROKEN",
                    },
                    {
                        "cabinetNumber": 26,
                        "xPos": 200,
                        "yPos": 500,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 27,
                        "xPos": 200,
                        "yPos": 400,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 28,
                        "xPos": 200,
                        "yPos": 300,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 29,
                        "xPos": 200,
                        "yPos": 200,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 30,
                        "xPos": 200,
                        "yPos": 100,
                        "status": "BROKEN",
                    },
                    {
                        "cabinetNumber": 31,
                        "xPos": 300,
                        "yPos": 1000,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 32,
                        "xPos": 300,
                        "yPos": 900,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 33,
                        "xPos": 300,
                        "yPos": 800,
                        "status": "OVERDUE",
                    },
                    {
                        "cabinetNumber": 34,
                        "xPos": 300,
                        "yPos": 700,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 35,
                        "xPos": 300,
                        "yPos": 600,
                        "status": "OVERDUE",
                    },
                    {
                        "cabinetNumber": 36,
                        "xPos": 300,
                        "yPos": 500,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 37,
                        "xPos": 300,
                        "yPos": 400,
                        "status": "AVAILABLE",
                    },
                    {
                        "cabinetNumber": 38,
                        "xPos": 300,
                        "yPos": 300,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 39,
                        "xPos": 300,
                        "yPos": 200,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 40,
                        "xPos": 300,
                        "yPos": 100,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 41,
                        "xPos": 400,
                        "yPos": 1000,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 42,
                        "xPos": 400,
                        "yPos": 900,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 43,
                        "xPos": 400,
                        "yPos": 800,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 44,
                        "xPos": 400,
                        "yPos": 700,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 45,
                        "xPos": 400,
                        "yPos": 600,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 46,
                        "xPos": 400,
                        "yPos": 500,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 47,
                        "xPos": 400,
                        "yPos": 400,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 48,
                        "xPos": 400,
                        "yPos": 300,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 49,
                        "xPos": 400,
                        "yPos": 200,
                        "status": "USING",
                    },
                    {
                        "cabinetNumber": 50,
                        "xPos": 400,
                        "yPos": 100,
                        "status": "USING",
                    }
                ]
            }

        return Response(floorInfo, status=status.HTTP_200_OK)

        return Response.status(status.HTTP_200_OK)
    
class CabinetTestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        cabinets.objects.update_or_create(
            user_id=users.objects.get(id=1),
            building_id=buildings.objects.get(name='가온관', floor=1),
            cabinet_number=1,
            status='USING',
            payable='FREE'
        )

        cabinet_histories.objects.update_or_create(
            user_id=users.objects.get(id=1),
            cabinet_id=cabinets.objects.get(building_id=1, cabinet_number=1),
            expired_at='2024-12-31 23:59:59'
        )

        cabinet_positions.objects.update_or_create(
            cabinet_id=cabinets.objects.get(building_id=1, cabinet_number=1),
            cabinet_x_pos=0,
            cabinet_y_pos=1000
        )

        return Response({"message": "cabinet created successfully"},status=status.HTTP_200_OK)


class CabinetLogView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 이력 조회'],
        request_body=None,
        responses={
            200: openapi.Response(
                description="성공적으로 조회되었습니다.",
                schema=CabinetLogDto(many=True)  # Ensure CabinetLogDto is a serializer
            ),
            401: openapi.Response(
                description="로그인 페이지로 이동",
                schema=openapi.Schema(type=openapi.TYPE_STRING)
            ),
            500: openapi.Response(
                description="컴포넌트들에 서버 통신 에러 문구 출력",
                schema=openapi.Schema(type=openapi.TYPE_STRING)
            ),
        }
    )
    def get(self, request):
        try:
            # Get the current user's student number
            student_number = request.user.student_number

            # Retrieve the user by student number
            user = users.find_one_userinfo_by_student_number(student_number=student_number)

            # Retrieve all cabinet history records associated with this user
            cabinet_history_infos = cabinet_histories.objects.filter(user_id=user.id)

            # Serialize the queryset with many=True
            cabinet_log_serializer = CabinetLogDto(cabinet_history_infos, many=True)

            return Response(cabinet_log_serializer.data, status=status.HTTP_200_OK)
        
        except users.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)