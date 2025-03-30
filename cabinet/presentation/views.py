from django.db.models import Q, F, Count, Case, When
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status
from core.util.pagination import paginate_data
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
import logging

from ..models import cabinets, cabinet_histories

from core.util.pagination import CabinetPagination

from cabinet.serializer import (CabinetDetailSerializer,
                                 CabinetFloorSerializer,
                                 CabinetHistorySerializer,
                                 CabinetSearchSerializer, 
                                 CabinetAdminReturnSerializer)


from cabinet.dto import (CabinetInfoQueryParamDto,
                         CabinetInfoDetailDto,
                         CabinetRentDto,
                         CabinetReturnDto,
                         CabinetSearchDetailDto,
                         CabinetSearchDto,
                         CabinetAdminReturnDto)

from authn.authentication import IsLoginUser
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
        dto = CabinetInfoQueryParamDto.create_validated(data=request.query_params)

        building = building_service.get_building(
            dto.validated_data.get('building'),
            dto.validated_data.get('floor')
        )
        
        cabinets = cabinet_service.get_cabinets_by_building_id(building.id)

        serializer = CabinetFloorSerializer(building=building, cabinets=cabinets)
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
            serialized_data=cabinet_serializer.data
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
        cabinet_histories_infos = cabinet_history_service.get_cabinet_histories_by_student_number(student_number=request.user.student_number)

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
                'cabinetId': openapi.Schema(
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
        successful_cabinets, failed_ids = cabinet_service.return_cabinets_by_ids(dto.validated_data.get('cabinetId'))
        
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
class CabinetAdminChangeStatusView(APIView, IsAdmin):
    permission_classes = [IsAuthenticated]
    authentication_classes = [IsLoginUser]

    @swagger_auto_schema(
        tags=['사물함 관리 (관리자)'],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['cabinetId', 'newStatus'],
            properties={
                'cabinetId': openapi.Schema(
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
                                    'reason': openapi.Schema(type=openapi.TYPE_STRING, nullable=True)
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
        # 관리자 권한 확인
        admin_check = self.check_admin_permission(request)
        if admin_check:
            return admin_check
            
        # 필수 파라미터 확인
        if 'cabinetId' not in request.data or 'newStatus' not in request.data:
            return Response(
                {"error": "cabinetId와 newStatus는 필수입니다"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        cabinet_ids = request.data.get('cabinetId')
        new_status = request.data.get('newStatus')
        reason = request.data.get('reason')
        
        if new_status == 'BROKEN' and not reason:
            return Response(
                {"error": "사물함 상태를 'BROKEN'으로 변경할 때는 reason 필드가 필수입니다"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # cabinetId 유효성 검증 (배열인지 확인)
        if not isinstance(cabinet_ids, list):
            return Response(
                {"error": "cabinetId는 반드시 배열 형태로 전달해야 합니다. 단일 사물함에 대해서도 [123]과 같이 배열로 전달하세요."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 상태 값 검증
        valid_statuses = ['AVAILABLE', 'USING', 'BROKEN', 'OVERDUE']
        if new_status not in valid_statuses:
            return Response(
                {"error": f"유효하지 않은 상태입니다. {valid_statuses} 중 하나여야 합니다"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_cabinets = []
        not_found_ids = []
        error_cabinets = []  # 상태 변경에 실패한 사물함 ID와 오류 메시지
        
        for cabinet_id in cabinet_ids:
            try:
                cabinet = cabinets.objects.get(id=cabinet_id)
                
                # 상태 변경 처리
                old_status = cabinet.status
                user_id = cabinet.user_id
                
                # 'USING' 상태로 변경하는데 사용자가 연결되어 있지 않은 경우
                if new_status == 'USING' and not user_id:
                    error_cabinets.append({
                        'id': cabinet_id,
                        'error': "사물함을 'USING' 상태로 변경하려면 먼저 사용자를 지정해야 합니다"
                    })
                    continue
                
                # 'AVAILABLE' 상태로 변경하는데 사용자가 연결되어 있는 경우
                if new_status == 'AVAILABLE' and user_id:
                    # 활성 대여 이력 종료
                    active_history = cabinet_histories.objects.filter(
                        cabinet_id=cabinet, 
                        ended_at=None
                    ).first()
                    
                    if active_history:
                        active_history.ended_at = timezone.now()
                        active_history.save()
                    
                    # update() 메서드를 사용하여 저장
                    cabinets.objects.filter(id=cabinet_id).update(
                        status=new_status,
                        user_id=None,
                        reason=reason if reason else None,  # reason 추가
                        updated_at=timezone.now()
                    )
                else:
                    # 일반적인 상태 업데이트
                    update_data = {
                        'status': new_status,
                        'updated_at': timezone.now()
                    }
                    
                    # reason이 있으면 추가
                    if reason is not None:
                        update_data['reason'] = reason
                    
                    # 업데이트 실행
                    cabinets.objects.filter(id=cabinet_id).update(**update_data)
                
                # 업데이트된 사물함 정보 저장
                updated_cabinet = cabinets.objects.select_related('building_id', 'user_id').get(id=cabinet_id)
                
                cabinet_info = {
                    'id': updated_cabinet.id,
                    'building': updated_cabinet.building_id.name if updated_cabinet.building_id else None,
                    'floor': updated_cabinet.building_id.floor if updated_cabinet.building_id else None,
                    'cabinetNumber': updated_cabinet.cabinet_number,
                    'status': updated_cabinet.status
                }
                
                updated_cabinets.append(cabinet_info)
                
            except cabinets.DoesNotExist:
                not_found_ids.append(cabinet_id)
        
        # 에러 메시지 구성
        error_messages = []
        if not_found_ids:
            error_messages.append(f"다음 ID의 사물함을 찾을 수 없습니다: {', '.join(map(str, not_found_ids))}")
        
        if error_cabinets:
            for error_cabinet in error_cabinets:
                error_messages.append(f"사물함 ID {error_cabinet['id']}: {error_cabinet['error']}")
        
        # 처리된 사물함이 없는 경우 에러 반환
        if not updated_cabinets:
            return Response(
                {"error": " ".join(error_messages)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 부분 성공인 경우 경고 메시지 추가
        message = "사물함 상태 변경이 완료되었습니다"
        if error_messages:
            message += f" (일부 사물함은 처리되지 않았습니다: {' '.join(error_messages)})"
        
        return Response({
            "message": message,
            "cabinets": updated_cabinets
        }, status=status.HTTP_200_OK)
    
class CabinetDashboardView(APIView, IsAdmin):
    permission_classes = [IsAuthenticated]
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
        # 관리자 권한 확인
        admin_check = self.check_admin_permission(request)
        if admin_check:
            return admin_check
        
        # 건물별로 상태별 사물함 수를 계산
        building_stats = cabinets.objects.select_related('building_id').values(
            'building_id__name'
        ).annotate(
            total=Count('id'),
            in_use=Count(Case(When(status='USING', then=1))),
            returned=Count(Case(When(status='AVAILABLE', then=1))),
            broken=Count(Case(When(status='BROKEN', then=1))),
            overdue=Count(Case(When(status='OVERDUE', then=1)))
        ).order_by('building_id__name')
        
        # 응답 형식 구성
        result = []
        for stat in building_stats:
            result.append({
                'name': stat['building_id__name'] or '미지정',
                'total': stat['total'],
                'using': stat['in_use'],
                'overdue': stat['overdue'],
                'broken': stat['broken'],
                'available': stat['returned']  # 'AVAILABLE' 상태는 'returned'와 동일
            })
        
        return Response({'buildings': result}, status=status.HTTP_200_OK)


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
        # 상태 파라미터 검증
        status_param = request.query_params.get('status')
        valid_statuses = ['AVAILABLE', 'USING', 'BROKEN', 'OVERDUE']
        
        if not status_param:
            return Response(
                {"error": "status 파라미터는 필수입니다"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if status_param not in valid_statuses:
            return Response(
                {"error": f"유효하지 않은 상태입니다. {valid_statuses} 중 하나여야 합니다"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 해당 상태의 모든 사물함 조회
        cabinets_qs = cabinets.objects.filter(
            status=status_param
        ).select_related('building_id', 'user_id')
        
        if not cabinets_qs.exists():
            return Response(
                {"error": f"상태가 {status_param}인 사물함을 찾을 수 없습니다"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # 페이지네이션 적용
        paginator = self.pagination_class()
        paginated_cabinets = paginator.paginate_queryset(cabinets_qs, request)
        
        # 응답 데이터 구성
        results = []
        for cabinet in paginated_cabinets:
            cabinet_data = {
                'id': cabinet.id,
                'building': cabinet.building_id.name if cabinet.building_id else None,
                'floor': cabinet.building_id.floor if cabinet.building_id else None,
                'section': cabinet.building_id.section,
                'position': {
                    'x': cabinet.cabinet_positions.cabinet_x_pos,
                    'y': cabinet.cabinet_positions.cabinet_y_pos
                } if hasattr(cabinet, 'cabinet_positions') and cabinet.cabinet_positions else None,
                'cabinetNumber': cabinet.cabinet_number,
                'status': cabinet.status,
                'reason' : cabinet.reason,
                'user': None,
            }
            
            # 사용자 정보 추가 (사용중인 경우)
            if cabinet.user_id:
                user = cabinet.user_id
                cabinet_data['user'] = {
                    'studentNumber': user.student_number if hasattr(user, 'student_number') else None,
                    'name': user.name if hasattr(user, 'name') else None
                }
                
                # 연체된 경우 대여 시작일, 만료일 추가
                if status_param == 'OVERDUE ':
                    rental_history = cabinet_histories.objects.filter(
                        cabinet_id=cabinet,
                        ended_at=None
                    ).first()

                    #print("status_param:", status_param)
                    #print("rental_history:", rental_history)
                    
                    if rental_history:
                        cabinet_data['rentalStartDate'] = rental_history.created_at
                        cabinet_data['overDate'] = rental_history.expired_at
                elif status_param == "BROKEN":
                    # select_related를 사용하여 관련 객체까지 함께 로드
                    rental_history = cabinet_histories.objects.select_related('cabinet_id').filter(
                        cabinet_id=cabinet,
                        ended_at=None
                    ).first()
                    
                    if rental_history:
                        cabinet_data['rentalStartDate'] = rental_history.created_at
                        cabinet_data['brokenDate'] = rental_history.cabinet_id.updated_at
            results.append(cabinet_data)
            
        return paginator.get_paginated_response(results)