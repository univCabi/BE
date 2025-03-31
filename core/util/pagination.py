from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from django.db import models


# 페이지네이션 클래스 정의
class CabinetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'pageSize'
    max_page_size = 100


def paginate_data(data, request, pagination_class=CabinetPagination, transform_func=None, serialized_data=None):
    """
    데이터를 페이지네이션하는 전역 유틸리티 함수
    
    Args:
        data (QuerySet or list): 페이지네이션할 데이터
        request (HttpRequest): HTTP 요청 객체
        pagination_class (Pagination): 사용할 페이지네이션 클래스 (기본값: CabinetPagination)
        transform_func (callable, optional): 각 객체를 변환하는 함수
        serialized_data (list, optional): 이미 직렬화된 데이터 (transform_func 대신 사용)
    
    Returns:
        Response: 페이지네이션된 응답
    """
    # 페이지 크기 파라미터 확인
    page_size = request.query_params.get('pageSize')
    if page_size and page_size.isdigit():
        request.query_params._mutable = True
        request.query_params[pagination_class.page_size_query_param] = page_size
        request.query_params._mutable = False
    
    # 페이지네이션 인스턴스 생성
    paginator = pagination_class()
    
    try:
        # 이미 직렬화된 데이터가 제공된 경우
        if serialized_data is not None:
            # 직렬화된 데이터를 페이지네이션
            page = paginator.paginate_queryset(serialized_data, request)
            return paginator.get_paginated_response(page)
            
        # 모델 인스턴스인 경우, transform_func이 반드시 필요함
        if (isinstance(data, models.Model) or 
            (isinstance(data, list) and len(data) > 0 and isinstance(data[0], models.Model))):
            if not callable(transform_func):
                raise ValueError("Model instances require a transform_func to be serializable")
                
        # 원본 데이터를 페이지네이션
        paginated_objects = paginator.paginate_queryset(data, request)
        
        # transform_func이 제공된 경우 데이터 변환
        if transform_func and callable(transform_func):
            results = [transform_func(obj) for obj in paginated_objects]
        else:
            results = paginated_objects
            
        # 페이지네이션된 응답 반환
        return paginator.get_paginated_response(results)
        
    except Exception as e:
        # 에러 로깅
        print(f"Pagination error: {str(e)}")
        
        # 에러 발생 시 기본 응답 생성
        try:
            # 페이지 크기 적용 (기본 30, 쿼리 파라미터 있으면 그 값 사용)
            limit = int(page_size) if page_size and page_size.isdigit() else 12
            limit = min(limit, 100)  # 최대 100개로 제한
            
            # 직렬화 방식에 따라 결과 준비
            if serialized_data is not None:
                results = serialized_data[:limit]
            elif transform_func and callable(transform_func):
                # 모델 인스턴스를 직렬화 가능한 형태로 변환
                if isinstance(data, models.QuerySet) or (
                    isinstance(data, list) and len(data) > 0 and isinstance(data[0], models.Model)
                ):
                    limited_data = data[:limit]
                    results = [transform_func(obj) for obj in limited_data]
                else:
                    results = data[:limit]
            else:
                # 직렬화 불가능한 경우 빈 결과 반환
                if isinstance(data, models.QuerySet) or (
                    isinstance(data, list) and len(data) > 0 and isinstance(data[0], models.Model)
                ):
                    results = []
                else:
                    results = data[:limit]
            
            # 전체 항목 수 계산
            if hasattr(data, '__len__'):
                count = len(data)
            elif hasattr(data, 'count') and callable(data.count):
                count = data.count()
            else:
                count = len(results)
                
            # 기본 페이지네이션 형식으로 응답
            return Response({
                "count": count,
                "next": None,
                "previous": None,
                "results": results
            })
        except Exception as fallback_error:
            print(f"Critical pagination error: {str(fallback_error)}")
            return Response({
                "count": 0,
                "next": None,
                "previous": None,
                "results": []
            })