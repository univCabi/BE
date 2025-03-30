from rest_framework.views import exception_handler
from rest_framework.response import Response
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from .base import ApplicationError

def global_exception_handler(exc, context):
    """글로벌 예외 핸들러"""
    # DRF 기본 핸들러 먼저 호출
    response = exception_handler(exc, context)
    
    if response is not None:
        return response
    
    # 애플리케이션 예외 처리
    if isinstance(exc, ApplicationError):
        data = {
            'error': exc.error_code,
            'message': str(exc),
        }
        
        if exc.details:
            data['details'] = exc.details
            
        return Response(data, status=exc.status_code)
    
    # Django 내장 예외 처리
    if isinstance(exc, DjangoValidationError):
        return Response({
            'error': 'validation_error',
            'message': 'Validation failed',
            'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc)
        }, status=400)
    
    if isinstance(exc, IntegrityError):
        return Response({
            'error': 'data_integrity_error',
            'message': str(exc)
        }, status=400)
    
    # 미처리 예외 - 로깅 후 일반 오류 응답
    import logging
    logger = logging.getLogger('django')
    logger.exception(exc)
    
    return Response({
        'error': 'server_error',
        'message': '서버 오류가 발생했습니다'
    }, status=500)