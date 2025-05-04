import json
import time
import logging
from django_redis import get_redis_connection

logger = logging.getLogger(__name__)

class AsyncResultManager:
    """비동기 작업 결과 관리자"""
    
    @staticmethod
    def set_result(task_id, result, expire_time=300):
        """비동기 작업 결과를 Redis에 저장"""
        redis_conn = get_redis_connection("default")
        key = f"cabinet:async:result:{task_id}"
        redis_conn.set(key, json.dumps(result), ex=expire_time)
        logger.debug(f"결과 저장 완료: {task_id}")
    
    @staticmethod
    def get_result(task_id, timeout=10, poll_interval=0.5):
        """Redis에서 비동기 작업 결과 조회 (timeout 동안 대기)"""
        redis_conn = get_redis_connection("default")
        key = f"cabinet:async:result:{task_id}"
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            result = redis_conn.get(key)
            if result:
                try:
                    return json.loads(result.decode('utf-8') if isinstance(result, bytes) else result)
                except json.JSONDecodeError:
                    logger.error(f"결과 JSON 파싱 실패: {task_id}")
                    return None
            time.sleep(poll_interval)
        
        logger.warning(f"결과 조회 타임아웃: {task_id}")
        return None
    
    @staticmethod
    def delete_result(task_id):
        """작업 결과 삭제"""
        redis_conn = get_redis_connection("default")
        key = f"cabinet:async:result:{task_id}"
        redis_conn.delete(key)
        logger.debug(f"결과 삭제 완료: {task_id}")