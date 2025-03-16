from django.db.models import Q, F
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
import logging

from .models import cabinets, buildings, cabinet_histories
from user.models import users
from authn.models import authns
from .serializers import (
    CabinetHistorySerializer, 
    CabinetFloorSerializer, 
    CabinetDetailSerializer
)
from .dto import (
    CabinetFloorQueryParamDto, 
    CabinetFloorDetailDto, 
    CabinetRentDto, 
    CabinetReturnDto, 
    SearchDetailDto, 
    SearchDto
)
from authn.authentication import IsLoginUser

logger = logging.getLogger(__name__)

# 페이지네이션 클래스 정의
class CabinetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'
    max_page_size = 100

class CabinetFloorView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 정보 조회'],
        query_serializer=CabinetFloorQueryParamDto,
        responses={
            200: openapi.Response(
                description="성공적으로 조회되었습니다.",
                schema=CabinetFloorSerializer
            ),
            404: openapi.Response(
                description="Building with the specified name and floor not found.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'error': openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description='Building with the specified name and floor not found.'
                        )
                    }
                )
            ),
        }
    )
    def get(self, request):
        cabinetFloorDto = CabinetFloorQueryParamDto(data=request.query_params)
        if not cabinetFloorDto.is_valid():
            return Response(cabinetFloorDto.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 해당 건물과 층을 가진 빌딩 조회
        building = buildings.objects.filter(
            name=cabinetFloorDto.validated_data.get('building'),
            floor=cabinetFloorDto.validated_data.get('floor')
        ).first()
        if not building:
            return Response(
                {"error": "Building with the specified name and floor not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 빌딩에 속한 모든 캐비닛 조회 (관련된 사용자 정보와 위치 정보도 함께 가져오기)
        cabinets_qs = cabinets.objects.filter(building_id=building).select_related('user_id', 'cabinet_positions')
        if not cabinets_qs.exists():
            return Response(
                {"error": "No cabinets found in the specified building and floor."},
                status=status.HTTP_404_NOT_FOUND
            )

        cabinet_floor_info = {
            "floor": building.floor,
            "section": building.section,
            "floorWidth": building.width,
            "floorHeight": building.height,
            "cabinets": cabinets_qs
        }
        cabinet_floor_serializer = CabinetFloorSerializer(cabinet_floor_info, context={'request': request})
        return Response(cabinet_floor_serializer.data, status=status.HTTP_200_OK)


class CabinetFloorDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 상세 정보 조회'],
        manual_parameters=[
            openapi.Parameter(
                'cabinetId', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_INTEGER, 
                description='사물함 ID', 
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="성공적으로 조회되었습니다.",
                schema=CabinetDetailSerializer
            ),
            400: openapi.Response(
                description="Cabinet ID parameter is required.",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'detail': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            404: openapi.Response(
                description="Cabinet not found.",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        cabinet_floor_detail_dto = CabinetFloorDetailDto(data=request.query_params)
        if not cabinet_floor_detail_dto.is_valid():
            return Response(
                {"detail": "Cabinet ID parameter is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        cabinet_id = cabinet_floor_detail_dto.validated_data.get('cabinetId')
        try:
            cabinet = cabinets.objects.select_related('building_id', 'user_id').get(id=cabinet_id)
        except cabinets.DoesNotExist:
            return Response(
                {"error": "Cabinet not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        cabinet_detail_serializer = CabinetDetailSerializer(cabinet, context={'request': request})
        return Response(cabinet_detail_serializer.data, status=status.HTTP_200_OK)


class CabinetRentView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 대여'],
        request_body=CabinetRentDto,
        responses={
            200: openapi.Response(
                description="Cabinet Rent Successful",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            400: openapi.Response(
                description="이미 대여한 사물함이 있는 경우",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            409: openapi.Response(
                description="해당 사물함이 대여중인 경우",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            404: openapi.Response(
                description="Cabinet not found",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def post(self, request):
        student_number = request.user.student_number
        cabinet_rent_dto = CabinetRentDto(data=request.data)
        if not cabinet_rent_dto.is_valid():
            return Response(cabinet_rent_dto.errors, status=status.HTTP_400_BAD_REQUEST)
        
        authns_info = authns.objects.filter(student_number=student_number).first()
        cabinet_id = cabinet_rent_dto.validated_data.get('cabinetId')
        
        if cabinet_histories.objects.filter(user_id=authns_info.user_id, ended_at=None).exists():
            return Response({"error": "Rented Other Cabinet"}, status=status.HTTP_400_BAD_REQUEST)
        if cabinet_histories.objects.filter(cabinet_id=cabinet_id, ended_at=None).exists():
            return Response({"error": "Cabinet is already rented"}, status=status.HTTP_409_CONFLICT)
        if not cabinets.objects.filter(id=cabinet_id).exists():
            return Response({"error": "Cabinet not found."}, status=status.HTTP_404_NOT_FOUND)
        
        cabinet = cabinets.objects.get(id=cabinet_id)
        cabinet_histories.objects.create(
            user_id=authns_info.user_id,
            cabinet_id=cabinet,
            expired_at=timezone.now() + timezone.timedelta(days=120)
        )
        cabinets.objects.filter(id=cabinet_rent_dto.validated_data.get('cabinetId')).update(
            status='USING', 
            user_id_id=authns_info.user_id
        )
        cabinet = cabinets.objects.select_related('building_id', 'user_id').get(id=cabinet_rent_dto.validated_data.get('cabinetId'))
        cabinet_detail_serializer = CabinetDetailSerializer(cabinet, context={'request': request})
        return Response(cabinet_detail_serializer.data, status=status.HTTP_200_OK)


class CabinetReturnView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 반납'],
        request_body=CabinetReturnDto,
        responses={
            200: openapi.Response(
                description="Cabinet Return Successful",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'message': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            400: openapi.Response(
                description="Cabinet is not rented",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            404: openapi.Response(
                description="Cabinet not found",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def post(self, request):
        student_number = request.user.student_number
        cabinet_return_dto = CabinetReturnDto(data=request.data)
        if not cabinet_return_dto.is_valid():
            return Response(cabinet_return_dto.errors, status=status.HTTP_400_BAD_REQUEST)
        
        authns_info = authns.objects.filter(student_number=student_number).first()
        cabinet_id = cabinet_return_dto.validated_data.get('cabinetId')
        try:
            cabinets.objects.get(id=cabinet_id)
        except cabinets.DoesNotExist:
            return Response({"error": "Cabinet not found."}, status=status.HTTP_404_NOT_FOUND)
        
        rental_history = cabinet_histories.objects.filter(
            user_id=authns_info.user_id, 
            cabinet_id=cabinet_id, 
            ended_at=None
        ).first()
        if not rental_history:
            return Response({"error": "Cabinet is not rented"}, status=status.HTTP_400_BAD_REQUEST)
        
        rental_history.ended_at = timezone.now()
        rental_history.save()
        cabinets.objects.filter(id=cabinet_id).update(status='AVAILABLE', user_id_id=None)
        cabinet = cabinets.objects.select_related('building_id', 'user_id').get(id=cabinet_id)
        cabinet_detail_serializer = CabinetDetailSerializer(cabinet, context={'request': request})
        return Response(cabinet_detail_serializer.data, status=status.HTTP_200_OK)


class CabinetSearchView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 검색 결과'],
        manual_parameters=[
            openapi.Parameter(
                'keyword', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_STRING, 
                description='검색어', 
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="검색 결과",
                schema=openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'building': openapi.Schema(type=openapi.TYPE_STRING),
                            'floor': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING)
                        }
                    )
                )
            ),
            400: openapi.Response(
                description="Invalid keyword parameter",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            )
        }
    )
    def get(self, request):
        search_dto = SearchDto(data=request.query_params)
        if not search_dto.is_valid():
            return Response(search_dto.errors, status=status.HTTP_400_BAD_REQUEST)
        keyword = search_dto.validated_data.get('keyword')
        if keyword.isdigit():
            q_objects = Q(cabinet_number__exact=keyword)
        else:
            q_objects = Q(building_id__name__contains=keyword)
        cabinet_info = cabinets.objects.filter(q_objects).select_related('building_id')[:6]
        data = [
            {
                "building": cabinet.building_id.name if cabinet.building_id else None,
                "floor": cabinet.building_id.floor if cabinet.building_id else None,
                "cabinetNumber": cabinet.cabinet_number,
            }
            for cabinet in cabinet_info
        ]
        return Response(data, status=status.HTTP_200_OK)


class CabinetSearchDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    # 페이지네이션 클래스 인스턴스 생성
    pagination_class = CabinetPagination

    @swagger_auto_schema(
        tags=['사물함 구체적인 검색 결과'],
        manual_parameters=[
            openapi.Parameter(
                'keyword', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_STRING, 
                description='검색어', 
                required=True
            ),
            openapi.Parameter(
                'page', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_INTEGER, 
                description='페이지 번호', 
                required=False
            ),
            openapi.Parameter(
                'pageSize', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_INTEGER, 
                description='페이지 크기', 
                required=False
            ),
        ],
        responses={
            200: openapi.Response(
                description="구체적인 검색 결과",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                        'results': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'building': openapi.Schema(type=openapi.TYPE_STRING),
                                    'floor': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="Invalid parameters",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            )
        }
    )
 
    def get(self, request):
        search_detail_dto = SearchDetailDto(data=request.query_params)

        if not search_detail_dto.is_valid():
            return Response(search_detail_dto.errors, status=status.HTTP_400_BAD_REQUEST)

        keyword = search_detail_dto.validated_data.get('keyword')

        # Q 객체를 사용하여 여러 필드에 대한 OR 조건 설정
        if keyword.isdigit():
            q_objects = Q(cabinet_number__exact=keyword)
        else:
            q_objects = Q(building_id__name__contains=keyword)

        # 조인된 buildings 정보도 함께 가져오기 위해 select_related 사용
        cabinet_info = cabinets.objects.filter(q_objects).select_related('building_id')

        print("cabinet_info: ", cabinet_info)
        
        # 페이지네이션 인스턴스 생성
        paginator = self.pagination_class()
        
        try:
            # 페이지네이션 수행
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
            
        except Exception as e:
            # 디버깅을 위한 오류 출력
            print(f"Pagination error: {str(e)}")
            
            # 페이지네이션 실패 시 전체 결과 반환
            data = [
                {
                    "building": cabinet.building_id.name if cabinet.building_id else None,
                    "floor": cabinet.building_id.floor if cabinet.building_id else None,
                    "cabinetNumber": cabinet.cabinet_number,
                }
                for cabinet in cabinet_info[:30]  # 안전을 위해 최대 30개만 반환
            ]
            
            return Response({
                "count": len(cabinet_info),
                "next": None,
                "previous": None,
                "results": data
            })


class CabinetHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]
    pagination_class = CabinetPagination

    @swagger_auto_schema(
        tags=['사물함 이력 조회'],
        responses={
            200: openapi.Response(
                description="성공적으로 조회되었습니다.",
                schema=CabinetHistorySerializer(many=True)
            ),
            401: openapi.Response(
                description="로그인 필요",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            500: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        try:
            student_number = request.user.student_number
            user = users.find_one_userinfo_by_student_number(student_number=student_number)
            cabinet_history_infos = cabinet_histories.objects.filter(user_id=user.id).order_by(
                F('ended_at').desc(nulls_first=True)
            )
            paginator = self.pagination_class()
            paginated_cabinet_history = paginator.paginate_queryset(cabinet_history_infos, request, view=self)
            cabinet_history_serializer = CabinetHistorySerializer(paginated_cabinet_history, many=True)
            return paginator.get_paginated_response(cabinet_history_serializer.data)
        except users.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class CabinetFindAll(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]
    
    pagination_class = CabinetPagination

    @swagger_auto_schema(
        tags=['사물함 전체 조회'],
        responses={
            200: openapi.Response(
                description="성공적으로 조회되었습니다.",
                schema=CabinetFloorSerializer
            ),
            404: openapi.Response(
                description="No cabinets found.",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        cabinets_qs = cabinets.objects.select_related('user_id', 'building_id').all()
        if not cabinets_qs.exists():
            return Response(
                {"error": "No cabinets found."},
                status=status.HTTP_404_NOT_FOUND
            )
        cabinet_floor_info = {
            "floor": "전체",
            "section": "전체",
            "floorWidth": 0,
            "floorHeight": 0,
            "cabinets": cabinets_qs
        }
        cabinet_floor_serializer = CabinetFloorSerializer(cabinet_floor_info, context={'request': request})
        return Response(cabinet_floor_serializer.data, status=status.HTTP_200_OK)

