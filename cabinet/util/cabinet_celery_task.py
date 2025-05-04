from celery import shared_task
from django_redis import get_redis_connection
import logging
from core.config.redis_lock import RedisLock
from cabinet.util.cabinet_async_result_manager import AsyncResultManager
from cabinet.util.cabinet_bookmark_sync_manager import BookmarkSyncManager

logger = logging.getLogger(__name__)

@shared_task
def process_cabinet_rental(cabinet_id, student_number, task_id=None):
    """
    사물함 대여 요청을 비동기적으로 처리
    
    Args:
        cabinet_id: 사물함 ID
        student_number: 학번
        task_id: 작업 추적을 위한 ID (없으면 Celery 작업 ID 사용)
    
    Returns:
        처리 결과 딕셔너리
    """
    
    logger.info(f"사물함 {cabinet_id} 대여 요청 처리 중 (학번: {student_number})")
    
    # 작업 ID 설정
    task_id = task_id or process_cabinet_rental.request.id
    
    redis_conn = get_redis_connection("default")
    processing_key = f"cabinet:processing:{cabinet_id}"
    
    try:
        lock_name = f"cabinet:{cabinet_id}:rent"
        
        with RedisLock(lock_name, expire_time=30) as lock:
            if lock.acquired:
                try:
                    # 사물함 대여 처리
                    from cabinet.business.cabinet_service import CabinetService
                    cabinet_service = CabinetService()
                    cabinet_service.rent_cabinet(cabinet_id, student_number)
                    
                    result = {
                        "status": "success", 
                        "cabinet_id": cabinet_id,
                        "student_number": student_number,
                        "message": f"사물함 {cabinet_id} 대여 성공"
                    }
                    
                    logger.info(f"사물함 {cabinet_id} 대여 성공 (학번: {student_number})")
                    
                    # 결과 저장
                    AsyncResultManager.set_result(task_id, result)
                    return result
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"사물함 {cabinet_id} 대여 실패: {error_msg}")
                    
                    result = {
                        "status": "error", 
                        "cabinet_id": cabinet_id,
                        "student_number": student_number,
                        "message": error_msg
                    }
                    
                    # 결과 저장
                    AsyncResultManager.set_result(task_id, result)
                    return result
            else:
                result = {
                    "status": "error", 
                    "cabinet_id": cabinet_id,
                    "student_number": student_number,
                    "message": "사물함 대여 처리를 위한 락 획득 실패"
                }
                
                logger.warning(f"사물함 {cabinet_id} 락 획득 실패")
                
                # 결과 저장
                AsyncResultManager.set_result(task_id, result)
                return result
    finally:
        # 처리 키 삭제
        redis_conn.delete(processing_key)

@shared_task
def process_cabinet_return(cabinet_id, student_number, task_id=None):
    """
    사물함 반납 요청을 비동기적으로 처리
    
    Args:
        cabinet_id: 사물함 ID
        student_number: 학번
        task_id: 작업 추적을 위한 ID (없으면 Celery 작업 ID 사용)
    
    Returns:
        처리 결과 딕셔너리
    """
    
    logger.info(f"사물함 {cabinet_id} 반납 요청 처리 중 (학번: {student_number})")
    
    # 작업 ID 설정
    task_id = task_id or process_cabinet_return.request.id
    
    redis_conn = get_redis_connection("default")
    processing_key = f"cabinet:processing:return:{cabinet_id}"
    
    try:
        lock_name = f"cabinet:{cabinet_id}:return"
        
        with RedisLock(lock_name, expire_time=10) as lock:
            if lock.acquired:
                try:
                    # 사물함 반납 처리
                    from cabinet.business.cabinet_service import CabinetService
                    cabinet_service = CabinetService()
                    cabinet_service.return_cabinet(cabinet_id, student_number)
                    
                    result = {
                        "status": "success", 
                        "cabinet_id": cabinet_id,
                        "student_number": student_number,
                        "message": f"사물함 {cabinet_id} 반납 성공"
                    }
                    
                    logger.info(f"사물함 {cabinet_id} 반납 성공 (학번: {student_number})")
                    
                    # 결과 저장
                    AsyncResultManager.set_result(task_id, result)
                    return result
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"사물함 {cabinet_id} 반납 실패: {error_msg}")
                    
                    result = {
                        "status": "error", 
                        "cabinet_id": cabinet_id,
                        "student_number": student_number,
                        "message": error_msg
                    }
                    
                    # 결과 저장
                    AsyncResultManager.set_result(task_id, result)
                    return result
            else:
                result = {
                    "status": "error", 
                    "cabinet_id": cabinet_id,
                    "student_number": student_number,
                    "message": "사물함 반납 처리를 위한 락 획득 실패"
                }
                
                logger.warning(f"사물함 {cabinet_id} 락 획득 실패")
                
                # 결과 저장
                AsyncResultManager.set_result(task_id, result)
                return result
    finally:
        # 처리 키 삭제
        redis_conn.delete(processing_key)

@shared_task(bind=True, max_retries=3)
def sync_bookmarks_to_database(self):
    """북마크 Redis -> DB 동기화 태스크"""
    try:
        logger.info("북마크 동기화 작업 시작")
        sync_manager = BookmarkSyncManager()
        result = sync_manager.sync_to_database()
        logger.info(f"북마크 동기화 작업 완료: {result}")
        return result
    except Exception as e:
        logger.error(f"북마크 동기화 중 오류 발생: {str(e)}")
        return {"status": "failed", "error": str(e)}