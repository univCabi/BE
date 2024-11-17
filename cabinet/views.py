from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_yasg import openapi

from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema


from .models import cabinets, buildings, cabinet_positions, cabinet_histories
from user.models import users
from .serializers import requestFindAllCabinetInfoByBuildingNameAndFloor, lentCabinetByUserIdAndCabinetId
from .serializers import CabinetLogDto
from authn.authentication import IsLoginUser

# Create your views here.

class CabinetMainView(APIView):
    @swagger_auto_schema(tags=['특정건물과 특정층의 사물함 정보를 반환합니다.'], 
                         query_serializer=requestFindAllCabinetInfoByBuildingNameAndFloor, 
                         responses={200: 'Success'})
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
        
#TODO: 추후에 user 정보 기반으로 검색 가능하도록 수정
class CabinetSearchView(APIView):
    permission_classes = [AllowAny]
    #permission_classes = [IsAuthenticated]
    #authentication_classes = [IsLoginUser]

    @swagger_auto_schema(tags=['사물함 검색 결과'], manual_parameters=[
        openapi.Parameter('keyword', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='검색어', required=True)
    ])
    def get(self, request):
        keyword = request.GET.get('keyword', '').strip()

        print("keyword:", keyword)

        if not keyword:
            return Response({"detail": "Keyword parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        elif len(keyword) < 2 and not keyword.isdigit():
            return Response({"detail": "Keyword must be at least 2 characters long."}, status=status.HTTP_400_BAD_REQUEST)

        # Q 객체를 사용하여 여러 필드에 대한 OR 조건 설정
        # keyword와 일치하는 사물함 정보를 검색
        if keyword.isdigit():
            q_objects = Q(cabinet_number__exact=keyword)
        else:
            q_objects = Q(building_id__name__contains=keyword)
        # keyword가 숫자인 경우 floor 필드도 필터링에 추가
        #if keyword.isdigit():
        #    q_objects |= Q(building_id__floor=int(keyword))

        # 조인된 buildings 정보도 함께 가져오기 위해 select_related 사용
        cabinet_info = cabinets.objects.filter(q_objects).select_related('building_id')[:6]

        # 디버깅 출력 (실제 배포 시에는 로깅 사용 권장)
        print("cabinet_info values:", list(cabinet_info.values()))

        # 필요한 정보만 직렬화하여 반환
        data = [
            {
                "building": cabinet.building_id.name if cabinet.building_id else None,
                "floor": cabinet.building_id.floor if cabinet.building_id else None,
                "cabinetNumber": cabinet.cabinet_number,
            }
            for cabinet in cabinet_info
        ]

        return Response(data, status=status.HTTP_200_OK)

# 당장은 모두 받기
# 나중에 무한 스크롤
#TODO: 추후의 유저가 해당 건물과 층에 대한 사물함을 대여할 수 있도록 수정
class CabinetRentView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]
    @swagger_auto_schema(tags=['사물함을 대여합니다.'], request_body=lentCabinetByUserIdAndCabinetId)
    def post(self, request):
    #building, floor, section, cabinetNumber, 
        # 유저 ID와 사물함 ID 받기

        student_number = request.user.student_number
        building = request.data.get('building')
        floor = request.data.get('floor')
        section = request.data.get('section')
        cabinetNumber = request.data.get('cabinetNumber')

        if not building or not floor or not section or not cabinetNumber:
            return Response({"error": "Invalid request body"}, status=status.HTTP_400_BAD_REQUEST)
        

        cabinetInfo = cabinets.objects.filter(building_id__name=building, building_id__floor=floor, building_id__section=section, cabinet_number=cabinetNumber)

        if not cabinetInfo:
            return Response({"error": "Cabinet not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # 이미 대여 중인지 확인
        if cabinetInfo.status == 'USING':
            return Response({"error": "Cabinet is already in use"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 이미 대여한 사물함이 있는지 확인
        if cabinet_histories.objects.filter(user_id=users.objects.get(student_number=student_number), ended_at=None):
            return Response({"error": "Cabinet is already rented"}, status=status.HTTP_400_BAD_REQUEST)

        # 대여 이력 생성
        cabinet_histories.objects.create(
            user_id=users.objects.get(student_number=student_number),
            cabinet_id=cabinetInfo,
            expired_at='2024-12-31 23:59:59'
        )
        
        return Response.status(status.HTTP_200_OK)

class CabinetReturnView(APIView):

    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response.status(status.HTTP_200_OK)


class CabinetPagination(PageNumberPagination):
    page_size = 20  # Number of items per page
    page_size_query_param = 'pageSize'  # Allow client to set page size via query parameter
    max_page_size = 100  # Maximum items per page

class CabinetSearchDetailView(APIView):
    permission_classes = [AllowAny]
    pagination_class = CabinetPagination
    #permission_classes = [IsAuthenticated]
    #authentication_classes = [IsLoginUser]

    @swagger_auto_schema(tags=['사물함 구체적인 검색 결과'], manual_parameters=[
        openapi.Parameter('keyword', openapi.IN_QUERY, type=openapi.TYPE_STRING, description='검색어', required=True),
        openapi.Parameter('page', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='페이지 번호', required=False),
        openapi.Parameter('pageSize', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, description='페이지 크기', required=False),
    ])
    def get(self, request):
        keyword = request.GET.get('keyword', '').strip()

        print("keyword:", keyword)

        if not keyword:
            return Response({"detail": "Keyword parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        elif len(keyword) < 2 and not keyword.isdigit():
            return Response({"detail": "Keyword must be at least 2 characters long."}, status=status.HTTP_400_BAD_REQUEST)

        # Q 객체를 사용하여 여러 필드에 대한 OR 조건 설정
        # keyword와 일치하는 사물함 정보를 검색

        if keyword.isdigit():
            q_objects = Q(cabinet_number__exact=keyword)
        else:
            q_objects = Q(building_id__name__contains=keyword)

        # keyword가 숫자인 경우 floor 필드도 필터링에 추가
        #if keyword.isdigit():
        #    q_objects |= Q(building_id__floor=int(keyword))

        # 조인된 buildings 정보도 함께 가져오기 위해 select_related 사용
        cabinet_info = cabinets.objects.filter(q_objects).select_related('building_id')

        # 디버깅 출력 (실제 배포 시에는 로깅 사용 권장)
        print("cabinet_info values:", list(cabinet_info.values()))

                # Initialize the paginator
        paginator = self.pagination_class()
        paginated_cabinets = paginator.paginate_queryset(cabinet_info, request)

        # 필요한 정보만 직렬화하여 반환
        data = [
            {
                "building": cabinet.building_id.name if cabinet.building_id else None,
                "floor": cabinet.building_id.floor if cabinet.building_id else None,
                "cabinetNumber": cabinet.cabinet_number,
            }
            for cabinet in paginated_cabinets
        ]

        return paginator.get_paginated_response(data)
    

class CabinetFloorView(APIView) :
    permission_classes = [AllowAny]
    def get(self, request):
        building_name = request.GET.get('building')
        floor = request.GET.get('floor')


        floorInfo = {
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


class PageNumberPagination(PageNumberPagination):
    page_size = 15  # Number of items per page
    page_size_query_param = 'pageSize'  # Allow client to set page size via query parameter
    max_page_size = 100  # Maximum items per page

class CabinetHistoryView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = [IsLoginUser]
    pagination_class = PageNumberPagination

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
            cabinet_history_serializer = CabinetLogDto(cabinet_history_infos, many=True)

            # Initialize the paginator
            paginator = self.pagination_class()
            paginated_cabinet_history = paginator.paginate_queryset(cabinet_history_infos, request)

            # Return the paginated response
            return paginator.get_paginated_response(cabinet_history_serializer.data)
        
        except users.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)