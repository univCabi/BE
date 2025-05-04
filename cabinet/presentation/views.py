from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
import logging

from cabinet.exceptions import CabinetAlreadyReturnedException, CabinetRentFailedException
from core.util.pagination import paginate_data, CabinetPagination


from cabinet.serializer import (CabinetDetailSerializer,
                                 CabinetInfoSerializer,
                                 CabinetHistorySerializer,
                                 CabinetSearchSerializer, 
                                 CabinetAdminReturnSerializer,
                                 CabinetStatisticsSerializer,
                                 CabinetStatusDetailSerializer,
                                 CabinetBookmarkListSerializer,
                                 CabinetBookmarkSerializer,
                                 )


from cabinet.dto import (CabinetInfoQueryParamDto,
                         CabinetInfoDetailDto,
                         CabinetRentDto,
                         CabinetReturnDto,
                         CabinetSearchDetailDto,
                         CabinetSearchDto,
                         CabinetAdminReturnDto,
                         CabinetAdminChangeStatusDto,
                         CabinetStatusSearchDto,
                         CabinetBookmarkDto)

from core.middleware.authentication import IsAdminUser, IsLoginUser
from authn.admin import IsAdmin

logger = logging.getLogger(__name__)

# 서비스 클래스 인스턴스 생성

from building.business.building_service import BuildingService
from cabinet.business.cabinet_service import CabinetService
from cabinet.business.cabinet_bookmark_service import CabinetBookmarkService
from cabinet.business.cabinet_history_service import CabinetHistoryService

building_service = BuildingService()
cabinet_service = CabinetService()
cabinet_bookmark_service = CabinetBookmarkService()
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
        
        try:
            # check_result=True로 비동기 결과 확인
            result = cabinet_service.request_rent_cabinet(
                cabinet_id=dto.validated_data.get('cabinetId'), 
                student_number=request.user.student_number,
                check_result=True
            )
            
            # 성공 시 캐비넷 정보 반환
            serializer = CabinetDetailSerializer(
                cabinet_service.get_cabinet_by_id(dto.validated_data.get('cabinetId')), 
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CabinetAlreadyReturnedException as e:
            # 이미 다른 사물함을 대여 중인 경우
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except CabinetRentFailedException as e:
            # 사물함이 이미 대여 중인 경우
            return Response({"error": str(e)}, status=status.HTTP_409_CONFLICT)

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


class CabinetAdminChangeStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        operation_id="admin_cabinet_change_status",
        tags=['Admin 사물함 관리'],
        request_body=CabinetAdminChangeStatusDto,
        responses={
            200: openapi.Response(
                description="사물함 상태 변경 성공 (전체 또는 일부)",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'cabinets': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'building': openapi.Schema(type=openapi.TYPE_STRING),
                                    'floor': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'cabinetNumber': openapi.Schema(type=openapi.TYPE_STRING),
                                    'brokenDate': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                    'userName': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                                }
                            )
                        ),
                        'errors': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        )
                    }
                )
            ),
            400: "잘못된 요청 또는 모든 사물함 상태 변경 실패",
            401: "인증 실패",
            403: "권한 없음 (관리자 아님)",
            500: "서버 오류"
        }
    )
    def post(self, request):
        """관리자 권한으로 사물함 상태를 변경합니다."""
        # DTO로 입력 데이터 검증
        dto = CabinetAdminChangeStatusDto.create_validated(data=request.data)
        
        cabinet_service = CabinetService()
        
        # 새 상태에 따라 서비스 메소드 호출 방식 분기
        if dto.validated_data.get('newStatus') in ['USING', 'OVERDUE']:
            # USING, OVERDUE 상태는 studentNumber가 필요
            successful_cabinets, failed_ids = cabinet_service.assign_cabinet_to_user(
                cabinet_id=dto.validated_data.get('cabinetIds')[0],  # 하나의 ID만 가능
                student_number=dto.validated_data.get('studentNumber'),
                status=dto.validated_data.get('newStatus')
            )
        elif dto.validated_data.get('newStatus') == 'BROKEN':
            # BROKEN 상태는 reason이 필요
            successful_cabinets, failed_ids = cabinet_service.change_cabinet_status_by_ids(
                cabinet_ids=dto.validated_data.get('cabinetIds'),
                new_status=dto.validated_data.get('newStatus'),
                reason=dto.validated_data.get('reason', '')  # 빈 문자열이라도 전달
            )
        else:  # AVAILABLE 상태
            # AVAILABLE 상태 변경 시 빈 문자열 reason 전달 (reason=None 대신)
            successful_cabinets, failed_ids = cabinet_service.change_cabinet_status_by_ids(
                cabinet_ids=dto.validated_data.get('cabinetIds'),
                new_status=dto.validated_data.get('newStatus'),
                reason=''  # 빈 문자열 전달
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
    

class CabinetBookmarkAddView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 즐겨찾기 추가'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cabinetId': openapi.Schema(type=openapi.TYPE_INTEGER, description='사물함 ID')
            },
            required=['cabinetId']
        ),
        responses={
            200: openapi.Response(
                description="즐겨찾기 추가 성공",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'isBookmark' : openapi.Schema(type=openapi.TYPE_BOOLEAN),
                })
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
    def post(self, request):
        dto = CabinetBookmarkDto.create_validated(data=request.data)

        cabinet_bookmark_service.add_bookmark(cabinet_id=dto.validated_data.get('cabinetId'), student_number=request.user.student_number)

        return Response({"isBookmark": True}, status=status.HTTP_200_OK)
    
class CabinetBookmarkRemoveView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 즐겨찾기 삭제'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'cabinetId': openapi.Schema(type=openapi.TYPE_INTEGER, description='사물함 ID')
            },
            required=['cabinetId']
        ),
        responses={
            200: openapi.Response(
                description="즐겨찾기 삭제 성공",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'isBookmark' : openapi.Schema(type=openapi.TYPE_BOOLEAN),
                })
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
    def post(self, request):
        dto = CabinetBookmarkDto.create_validated(data=request.data)

        cabinet_bookmark_service.remove_bookmark(cabinet_id=dto.validated_data.get('cabinetId'), student_number=request.user.student_number)

        return Response({"isBookmark": False}, status=status.HTTP_200_OK)
    

class CabinetBookmarkListView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 즐겨찾기 조회'],
        responses={
            200: openapi.Response(
                description="즐겨찾기 조회 성공",
                schema=CabinetBookmarkListSerializer(many=True)
            ),
            404: openapi.Response(
                description="즐겨찾기를 찾을 수 없음",
                schema=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    'error': openapi.Schema(type=openapi.TYPE_STRING)
                })
            ),
        }
    )
    def get(self, request):
        bookmarks = cabinet_bookmark_service.get_bookmarks(student_number=request.user.student_number)

        print(f"bookmarks: {bookmarks}")

        serializer = CabinetBookmarkListSerializer(bookmarks, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)