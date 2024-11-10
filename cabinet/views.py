from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status

from .serializers import requestFindAllCabinetInfoByBuildingNameAndFloor, lentCabinetByUserIdAndCabinetId, returnCabinetByUserIdAndCabinetId, searchCabinetAndBuildingByKeyWord, findAllCabinetHistoryByUserId, cabinetInfoSerializer, floorInfoItemSerializer, floorInfoSerializer, responseFindAllCabinetInfoByBuildingNameAndFloor
from .models import cabinets, buildings, cabinet_positions

from drf_yasg.utils import swagger_auto_schema



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