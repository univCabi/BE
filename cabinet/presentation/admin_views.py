from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django_redis import get_redis_connection
from core.middleware.authentication import IsLoginUser
from authn.admin import IsAdmin
import logging
from django.conf import settings
from celery.result import AsyncResult

logger = logging.getLogger(__name__)

class CabinetOperationsMonitorView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    authentication_classes = [IsLoginUser]
    
    def get(self, request):
        """Get status of current cabinet operations"""
        try:
            redis_conn = get_redis_connection("default")
            
            # Get all processing keys
            processing_keys = []
            for key in redis_conn.keys("cabinet:processing:*"):
                processing_keys.append({
                    'key': key.decode('utf-8'),
                    'value': redis_conn.get(key).decode('utf-8'),
                    'ttl': redis_conn.ttl(key)
                })
            
            # Get all lock keys
            lock_keys = []
            for key in redis_conn.keys("cabinet:lock:*"):
                lock_keys.append({
                    'key': key.decode('utf-8'),
                    'value': redis_conn.get(key).decode('utf-8'),
                    'ttl': redis_conn.ttl(key)
                })
            
            # Get task status if we have task IDs in the query
            task_statuses = {}
            task_ids = request.query_params.getlist('task_id')
            for task_id in task_ids:
                try:
                    result = AsyncResult(task_id)
                    task_statuses[task_id] = {
                        'status': result.status,
                        'result': result.result if result.ready() else None,
                    }
                except Exception as e:
                    task_statuses[task_id] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return Response({
                'processing_keys': processing_keys,
                'lock_keys': lock_keys,
                'task_statuses': task_statuses,
                'worker_config': {
                    'use_threaded': getattr(settings, 'CABINET_USE_THREADED_PROCESSING', False),
                    'celery_broker': settings.CELERY_BROKER_URL,
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error retrieving operations status: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve operations status.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )