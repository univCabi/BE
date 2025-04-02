from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import logging

from core.util.pagination import paginate_data, CabinetPagination


from cabinet.serializer import (CabinetDetailSerializer,
                                 CabinetInfoSerializer,
                                 CabinetHistorySerializer,
                                 CabinetSearchSerializer, 
                                 CabinetAdminReturnSerializer,
                                 CabinetStatisticsSerializer,
                                 CabinetStatusDetailSerializer)


from cabinet.dto import (CabinetInfoQueryParamDto,
                         CabinetInfoDetailDto,
                         CabinetRentDto,
                         CabinetReturnDto,
                         CabinetSearchDetailDto,
                         CabinetSearchDto,
                         CabinetAdminReturnDto,
                         CabinetAdminChangeStatusDto,
                         CabinetStatusSearchDto)

from core.middleware.authentication import IsLoginUser
from authn.admin import IsAdmin

logger = logging.getLogger(__name__)

# 서비스 클래스 인스턴스 생성

from building.business.building_service import BuildingService
from cabinet.business.cabinet_service import CabinetService
from cabinet.business.cabinet_history_service import CabinetHistoryService

cabinet_service = CabinetService()
building_service = BuildingService()
cabinet_history_service = CabinetHistoryService()

class CabinetInfoView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 정보 조회'],
        query_serializer=CabinetInfoQueryParamDto,
        manual_parameters=[
            openapi.Parameter(
                'building', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_STRING, 
                description='건물 이름',
                required=True
            ),
            openapi.Parameter(
                'floors', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_INTEGER),
                description='층 정보',
                required=True
            ),
        ],
        responses={
            200: openapi.Response(
                description="성공적으로 조회되었습니다.",
                schema=CabinetInfoSerializer
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
        dto = CabinetInfoQueryParamDto.create_validated(data=request.query_params)
        
        # 건물 정보 가져오기 (여러 층 지원)
        buildings_data = building_service.get_buildings_with_floors(
            dto.validated_data.get('building'),
            dto.validated_data.get('floors')
        )
        
        # 건물 ID 목록 가져오기
        building_ids = list(buildings_data.values_list('id', flat=True))
        
        # 캐비넷 정보 가져오기
        cabinets_data = cabinet_service.get_cabinets_by_building_ids(building_ids)
        
        # 층별로 그룹화된 건물 정보
        buildings_by_floor = {
            building.floor: building for building in buildings_data
        }
        
        serializer = CabinetInfoSerializer(
            instance=cabinets_data,
            many=True,
            context={
                'request': request, 
                'buildings': buildings_data,
                'buildings_by_floor': buildings_by_floor
            }
        )
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class CabinetInfoDetailView(APIView):
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
        dto = CabinetInfoDetailDto.create_validated(data=request.query_params)

        cabinet = cabinet_service.get_cabinet_by_id(dto.validated_data.get('cabinetId'))

        serializer = CabinetDetailSerializer(cabinet, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        dto = CabinetRentDto.create_validated(data=request.data)

        cabinet_service.rent_cabinet(cabinet_id=dto.validated_data.get('cabinetId'), student_number=request.user.student_number)

        serializer = CabinetDetailSerializer(cabinet_service.get_cabinet_by_id(dto.validated_data.get('cabinetId')), context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


#TODO: isMine 필드 변경
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
        dto = CabinetReturnDto.create_validated(data=request.data)

        cabinet_service.return_cabinet(cabinet_id=dto.validated_data.get('cabinetId'), student_number=request.user.student_number)

        serializer = CabinetDetailSerializer(cabinet_service.get_cabinet_by_id(dto.validated_data.get('cabinetId')), context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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
        dto = CabinetSearchDto.create_validated(data=request.query_params)

        #TODO: 개수 제한 처리
        cabinet_info = cabinet_service.search_cabinet(dto.validated_data.get('keyword'))[:6]

        serializer = CabinetSearchSerializer(cabinet_info, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CabinetSearchDetailView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

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
        dto = CabinetSearchDetailDto.create_validated(data=request.query_params)

        cabinet_info = cabinet_service.search_cabinet(dto.validated_data.get('keyword'))

        cabinet_serializer = CabinetSearchSerializer(cabinet_info, many=True)

        return paginate_data(
            data=cabinet_info,
            request=request,
            serialized_data=cabinet_serializer.data,
        )


class CabinetHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 이력 조회'],
        manual_parameters=[
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
        cabinet_histories_infos = cabinet_history_service.get_cabinet_histories_by_student_number(
            student_number=request.user.student_number
            )

        serializer = CabinetHistorySerializer(cabinet_histories_infos, many=True)

        return paginate_data(
            data=cabinet_histories_infos,
            request=request,
            serialized_data=serializer.data
        )

class CabinetFindAll(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]
    
    pagination_class = CabinetPagination

    @swagger_auto_schema(
        tags=['사물함 전체 조회'],
        manual_parameters=[
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
                description="성공적으로 조회되었습니다.",
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
            404: openapi.Response(
                description="No cabinets found.",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        cabinet_infos = cabinet_service.get_all_cabinets()
        serializer = CabinetSearchSerializer(cabinet_infos, many=True)
        return paginate_data(
            data=cabinet_infos,
            request=request,
            serialized_data=serializer.data
        )
    

class CabinetAdminReturnView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 관리 (관리자)'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cabinetIds': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='반납할 사물함 ID 목록 (하나의 사물함만 반납하더라도 배열로 전달)'
                )
            },
            required=['cabinetId']  # cabinetId만 필수
        ),
        responses={
            200: openapi.Response(
                description="사물함 반납 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'cabinets': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'building': openapi.Schema(type=openapi.TYPE_STRING),
                                    'floor': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING)
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            404: openapi.Response(
                description="사물함 또는 사용자를 찾을 수 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            }
        )
    
    #TODO: business layer로 이동 해야는지 가치판단 필요 
    def post(self, request):
        # DTO로 입력 데이터 검증
        dto = CabinetAdminReturnDto.create_validated(data=request.data)
        
        # 서비스 메소드 호출하여 결과 받기
        successful_cabinets, failed_ids = cabinet_service.return_cabinets_by_ids(dto.validated_data.get('cabinetIds'))
        
        # 에러 메시지 구성
        error_messages = []
        for failed in failed_ids:
            error_messages.append(f"사물함 ID {failed['id']}: {failed['reason']}")
        
        # 응답 데이터 준비
        response_data = {}
        
        # 성공한 사물함이 있으면 시리얼라이저로 변환
        if successful_cabinets:
            serializer = CabinetAdminReturnSerializer(successful_cabinets, many=True)
            response_data["cabinets"] = serializer.data
            
            # 메시지 구성
            if error_messages:
                response_data["message"] = f"일부 사물함 반납 처리가 완료되었습니다. (처리된 개수: {len(successful_cabinets)})"
                response_data["errors"] = error_messages
            else:
                response_data["message"] = f"모든 사물함 반납 처리가 완료되었습니다. (처리된 개수: {len(successful_cabinets)})"
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        # 모든 사물함 처리에 실패한 경우
        else:
            response_data["error"] = "모든 사물함 반납 처리에 실패했습니다."
            response_data["details"] = error_messages
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


# 2. 관리자 사물함 상태 변경 API (다중 처리 지원)
#TODO: dto, serializer 추가
class CabinetAdminChangeStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 관리 (관리자)'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['cabinetIds', 'newStatus'],
            properties={
                'cabinetIds': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_INTEGER),
                    description='상태를 변경할 사물함 ID 목록 (하나의 사물함만 변경하더라도 배열로 전달)'
                ),
                'newStatus': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    description='새 상태 (AVAILABLE, USING, BROKEN, OVERDUE)',
                    enum=['AVAILABLE', 'USING', 'BROKEN', 'OVERDUE']
                ),
                'reason': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='사물함 상태 변경 이유',
                    nullable=True
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="사물함 상태 변경 성공",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'cabinets': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'building': openapi.Schema(type=openapi.TYPE_STRING),
                                    'floor': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'reason': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'brokenDate': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            404: openapi.Response(
                description="사물함을 찾을 수 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def post(self, request):
            # DTO로 입력 데이터 검증
            dto = CabinetAdminChangeStatusDto.create_validated(data=request.data)
            
            # 서비스 메소드 호출하여 결과 받기
            successful_cabinets, failed_ids = cabinet_service.change_cabinet_status_by_ids(
                dto.validated_data.get('cabinetIds'), 
                dto.validated_data.get('newStatus'), 
                dto.validated_data.get('reason')
            )
            
            # 에러 메시지 구성
            error_messages = []
            for failed in failed_ids:
                error_messages.append(f"사물함 ID {failed['id']}: {failed['reason']}")
            
            # 응답 데이터 준비
            response_data = {}
            
            # 성공한 사물함이 있으면 시리얼라이저로 변환
            if successful_cabinets:
                # CabinetAdminReturnSerializer 형식에 맞게 시리얼라이즈
                serializer = CabinetAdminReturnSerializer(successful_cabinets, many=True)
                response_data["cabinets"] = serializer.data
                
                # 메시지 구성
                if error_messages:
                    response_data["message"] = f"일부 사물함 상태 변경이 완료되었습니다. (처리된 개수: {len(successful_cabinets)})"
                    response_data["errors"] = error_messages
                else:
                    response_data["message"] = f"모든 사물함 상태 변경이 완료되었습니다. (처리된 개수: {len(successful_cabinets)})"
                
                return Response(response_data, status=status.HTTP_200_OK)
            
            # 모든 사물함 처리에 실패한 경우
            else:
                response_data["error"] = "모든 사물함 상태 변경에 실패했습니다."
                response_data["details"] = error_messages
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


class CabinetDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 관리 (관리자)'],
        responses={
            200: openapi.Response(
                description="건물별 사물함 사용 현황",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'buildings': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'name': openapi.Schema(type=openapi.TYPE_STRING),
                                    'total': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'using': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'overdue': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'broken': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'available': openapi.Schema(type=openapi.TYPE_INTEGER),
                                }
                            )
                        )
                    }
                )
            ),
            403: openapi.Response(
                description="권한 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        cabinet_stats = cabinet_service.get_cabinet_statistics()
        
        # 시리얼라이저로 응답 데이터 형식화
        response_data = {'buildings': cabinet_stats}
        serializer = CabinetStatisticsSerializer(response_data)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class CabinetStatusSearchView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]
    pagination_class = CabinetPagination
    
    @swagger_auto_schema(
        tags=['사물함 상태별 조회'],
        manual_parameters=[
            openapi.Parameter(
                'status', 
                openapi.IN_QUERY, 
                type=openapi.TYPE_STRING, 
                description='조회할 사물함 상태 (AVAILABLE, USING, BROKEN, OVERDUE)', 
                required=True,
                enum=['AVAILABLE', 'USING', 'BROKEN', 'OVERDUE']
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
                description="상태별 사물함 조회 결과",
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
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'building': openapi.Schema(type=openapi.TYPE_STRING),
                                    'floor': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'section': openapi.Schema(type=openapi.TYPE_STRING),
                                    'position': openapi.Schema(type=openapi.TYPE_STRING),
                                    'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING),
                                    'status': openapi.Schema(type=openapi.TYPE_STRING),
                                    'user': openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'studentNumber': openapi.Schema(type=openapi.TYPE_STRING),
                                            'name': openapi.Schema(type=openapi.TYPE_STRING)
                                        },
                                        nullable=True
                                    ),
                                    'reason': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'rentalStartDate' : openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'overDate' : openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                }
                            )
                        )
                    }
                )
            ),
            400: openapi.Response(
                description="잘못된 요청",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
            404: openapi.Response(
                description="사물함을 찾을 수 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        # DTO로 입력 데이터 검증
        dto = CabinetStatusSearchDto.create_validated(data=request.query_params)
        cabinets_data = cabinet_service.get_cabinets_by_status(dto.validated_data.get('status'))
        
        # 페이지네이션 적용
        paginator = self.pagination_class()
        paginated_cabinets = paginator.paginate_queryset(cabinets_data, request)
        
        # 시리얼라이저로 응답 데이터 형식화
        serializer = CabinetStatusDetailSerializer(paginated_cabinets, many=True)
        
        return paginator.get_paginated_response(serializer.data)