import threading
import queue
import logging
import time
from django_redis import get_redis_connection
from cabinet.util.cabinet_async_result_manager import AsyncResultManager

logger = logging.getLogger(__name__)

class WorkerThread(threading.Thread):
    def __init__(self, task_queue, name=None):
        threading.Thread.__init__(self, name=name)
        self.task_queue = task_queue
        self.daemon = True
        self.running = True

    def run(self):
        logger.info(f"Worker thread {self.name} started")
        while self.running:
            try:
                # Get task from queue with timeout to allow for thread shutdown
                task, args, kwargs = self.task_queue.get(timeout=1)
                try:
                    result = task(*args, **kwargs)
                    logger.info(f"Thread {self.name} completed task {task.__name__} with result: {result}")
                except Exception as e:
                    logger.error(f"Thread {self.name} error processing task {task.__name__}: {str(e)}")
                finally:
                    self.task_queue.task_done()
            except queue.Empty:
                # No task available, just continue looping
                pass
        logger.info(f"Worker thread {self.name} stopped")

    def stop(self):
        self.running = False

class CabinetThreadPool:
    """Thread pool for processing cabinet operations concurrently"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CabinetThreadPool, cls).__new__(cls)
            cls._instance.init()
        return cls._instance
    
    def init(self):
        self.task_queue = queue.Queue()
        self.workers = []
        self.num_workers = 5  # Number of worker threads
        self.running = False
        self.lock = threading.Lock()  # For thread-safe operations
    
    def start(self):
        """Start the worker threads"""
        with self.lock:
            if self.running:
                return
                
            self.running = True
            # 이미 실행 중인 워커 개수 확인
            active_workers = [w for w in self.workers if w.is_alive()]
            needed_workers = self.num_workers - len(active_workers)
            
            # 필요한 만큼만 워커 추가
            for i in range(needed_workers):
                worker = WorkerThread(self.task_queue, name=f"cabinet-worker-{len(self.workers)}")
                worker.start()
                self.workers.append(worker)
            
            logger.info(f"워커 스레드 {needed_workers}개 시작됨 (총 {len(self.workers)}개)")
    
    def stop(self):
        """Stop the worker threads"""
        if not self.running:
            return
            
        self.running = False
        for worker in self.workers:
            worker.stop()
        
        # Wait for all threads to complete
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5)
        
        # Clear the workers list
        self.workers = []
        logger.info("Stopped all worker threads")
    
    def add_rental_task(self, cabinet_id, student_number, task_id=None):
        """Add a cabinet rental task to the queue with task ID"""
        if task_id is None:
            task_id = f"rental-{int(time.time())}-{cabinet_id}-{student_number}"
            
        redis_conn = get_redis_connection("default")
        processing_key = f"cabinet:processing:{cabinet_id}"
        
        try:
            # 이전 작업 결과가 있으면 삭제
            AsyncResultManager.delete_result(task_id)
            
            # 처리 중으로 표시 (이미 설정되어 있지 않은 경우만)
            if not redis_conn.get(processing_key):
                redis_conn.set(processing_key, student_number, ex=15)
            
            # 작업 큐에 추가
            self.task_queue.put((self._process_rental, (cabinet_id, student_number, task_id), {}))
            logger.info(f"사물함 {cabinet_id} 대여 작업이 큐에 추가됨 (작업 ID: {task_id})")
            return task_id
        except Exception as e:
            logger.error(f"대여 작업 추가 실패: {str(e)}")
            return None
    
    def _process_rental(self, cabinet_id, student_number, task_id):
        """Process a cabinet rental in this thread and store the result"""
        redis_conn = get_redis_connection("default")
        processing_key = f"cabinet:processing:{cabinet_id}"
        
        try:
            from cabinet.business.cabinet_service import CabinetService
            cabinet_service = CabinetService()
            cabinet_service.rent_cabinet(cabinet_id, student_number)
            # 성공 결과 저장
            AsyncResultManager.set_result(task_id, {
                "status": "success",
                "cabinet_id": cabinet_id,
                "student_number": student_number,
                "message": f"사물함 {cabinet_id} 대여 성공"
            })
            logger.info(f"사물함 {cabinet_id} 대여 성공 (학번: {student_number})")
            return True
        except Exception as e:
            # 실패 결과 저장
            logger.error(f"Error in worker thread for cabinet {cabinet_id}: {str(e)}")
            return self._handle_exception(e, cabinet_id, student_number, task_id)
        finally:
            # Clean up the processing key
            redis_conn.delete(processing_key)

    def _process_return(self, cabinet_id, student_number, task_id):
        """스레드에서 사물함 반납 처리"""
        redis_conn = get_redis_connection("default")
        processing_key = f"cabinet:processing:return:{cabinet_id}"
        
        try:
            # 순환 참조 방지를 위한 지연 임포트
            from cabinet.business.cabinet_service import CabinetService
            cabinet_service = CabinetService()
            
            # 사물함 반납 처리
            cabinet_service.return_cabinet(cabinet_id, student_number)
            
            # 성공 결과 저장
            result = {
                "status": "success",
                "cabinet_id": cabinet_id,
                "student_number": student_number,
                "message": f"사물함 {cabinet_id} 반납 성공"
            }
            AsyncResultManager.set_result(task_id, result)
            
            logger.info(f"사물함 {cabinet_id} 반납 성공 (학번: {student_number})")
            return True
        except Exception as e:
            # 실패 결과 저장
            error_msg = str(e)
            logger.error(f"사물함 {cabinet_id} 반납 실패: {error_msg}")
            
            result = {
                "status": "error",
                "cabinet_id": cabinet_id,
                "student_number": student_number,
                "message": error_msg
            }
            AsyncResultManager.set_result(task_id, result)
            
            return False
        finally:
            # 처리 키 삭제
            redis_conn.delete(processing_key)

    def _handle_exception(self, exception, cabinet_id, student_number, task_id):
        """예외 정보를 저장하는 헬퍼 메서드"""
        from core.exception.base import ApplicationError
        from cabinet.util.cabinet_async_result_manager import AsyncResultManager
        
        # 로그 기록
        logger.error(f"Error in cabinet operation (ID: {cabinet_id}): {str(exception)}")
        
        # 예외 정보 구성
        error_info = {
            "status": "error",
            "cabinet_id": cabinet_id,
            "student_number": student_number,
        }
        
        # 예외 클래스 정보 저장 (모듈 경로와 클래스명)
        error_info["exception_module"] = exception.__class__.__module__
        error_info["exception_class"] = exception.__class__.__name__
        error_info["message"] = str(exception)
        
        # ApplicationError 상속 클래스인 경우 추가 정보 포함
        if hasattr(exception, 'error_code'):
            error_info["error_code"] = getattr(exception, 'error_code', 'unknown_error')
        
        if hasattr(exception, 'status_code'):
            error_info["status_code"] = getattr(exception, 'status_code', 500)
        
        # 디테일 정보가 있으면 포함
        if hasattr(exception, 'details'):
            error_info["details"] = getattr(exception, 'details', None)
        
        # 결과 저장
        AsyncResultManager.set_result(task_id, error_info)
        return False  # 작업 실패 반환