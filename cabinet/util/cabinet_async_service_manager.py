import logging
import threading
import subprocess
import time
import atexit
import os
import signal
from django.conf import settings
from django_redis import get_redis_connection
from cabinet.util.worker_pool import CabinetThreadPool
from cabinet.util.cabinet_kafka_rent_consumer import CabinetRentConsumer

logger = logging.getLogger(__name__)

class AsyncServiceManager:
    """비동기 서비스 관리자"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AsyncServiceManager, cls).__new__(cls)
            cls._instance.init()
        return cls._instance
    
    def init(self):
        """초기화"""
        self.thread_pool = None
        self.kafka_consumer = None
        self.celery_worker_process = None
        self.running = False
        self.monitor_thread = None
        self.services_status = {
            'thread_pool': False,
            'celery': False,
            'kafka': False
        }
        
        # 종료 시 정리 함수 등록
        atexit.register(self.stop_all)
        
    
    def _handle_signal(self, signum, frame):
        """시그널 처리 핸들러"""
        logger.info(f"시그널 {signum} 수신: 서비스 종료 중...")
        self.stop_all()
    
    def start_all(self, skip_celery=False, skip_kafka=False, purge=False):
        """모든 비동기 서비스 시작"""
        if self.running:
            logger.warning("서비스가 이미 실행 중입니다.")
            return False
        
        self.running = True
        
        # Redis 서비스 상태 키 초기화
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.set("cabinet:service:status", "starting", ex=3600)
        except Exception as e:
            logger.error(f"Redis 연결 실패: {str(e)}")
            self.running = False
            return False
        
        # 1. 스레드 풀 시작
        self.start_thread_pool()
        
        # 2. Celery 워커 시작 (선택적)
        if not skip_celery:
            if purge:
                self.purge_celery_queue()
            self.start_celery_worker()
        
        # 3. Kafka 소비자 시작 (선택적)
        if not skip_kafka:
            self.start_kafka_consumer()
        
        redis_conn.set("cabinet:service:status", "running", ex=3600)
        logger.info("모든 비동기 서비스가 시작되었습니다.")
        
        # 상태 모니터링 스레드 시작
        self.monitor_thread = threading.Thread(target=self._monitor_services)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        return True
    
    def stop_all(self):
        """모든 비동기 서비스 종료"""
        if not self.running:
            return
            
        self.running = False
        logger.info("비동기 서비스 종료 중...")
        
        # 1. Kafka 소비자 종료
        if self.kafka_consumer:
            try:
                logger.info("Kafka 소비자 종료 중...")
                self.kafka_consumer.stop()
                self.services_status['kafka'] = False
            except Exception as e:
                logger.error(f"Kafka 소비자 종료 실패: {str(e)}")
        
        # 2. Celery 워커 종료
        if self.celery_worker_process:
            try:
                logger.info("Celery 워커 종료 중...")
                self.celery_worker_process.terminate()
                self.celery_worker_process.wait(timeout=5)
                self.services_status['celery'] = False
            except Exception as e:
                logger.error(f"Celery 워커 종료 실패: {str(e)}")
        
        # 3. 스레드 풀 종료
        if self.thread_pool:
            try:
                logger.info("스레드 풀 종료 중...")
                self.thread_pool.stop()
                self.services_status['thread_pool'] = False
            except Exception as e:
                logger.error(f"스레드 풀 종료 실패: {str(e)}")
        
        # Redis 상태 업데이트
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.set("cabinet:service:status", "stopped", ex=3600)
        except Exception:
            pass
            
        logger.info("모든 비동기 서비스가 종료되었습니다.")
    
    def start_thread_pool(self):
        """스레드 풀 시작"""
        try:
            logger.info("스레드 풀 시작 중...")
            self.thread_pool = CabinetThreadPool()
            self.thread_pool.start()
            self.services_status['thread_pool'] = True
            
            # Redis에 상태 저장
            redis_conn = get_redis_connection("default")
            redis_conn.set("cabinet:service:thread_pool", "running", ex=3600)
            
            logger.info(f"스레드 풀 시작 완료 ({self.thread_pool.num_workers}개 워커)")
            return True
        except Exception as e:
            logger.error(f"스레드 풀 시작 실패: {str(e)}")
            return False
    
    def purge_celery_queue(self):
        """Celery 큐 비우기"""
        try:
            logger.info("Celery 큐 비우는 중...")
            subprocess.run(
                ["celery", "-A", "core", "purge", "-f"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("Celery 큐 비우기 완료")
            return True
        except subprocess.CalledProcessError as e:
            logger.warning(f"Celery 큐 비우기 실패: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")
            return False
        except Exception as e:
            logger.error(f"Celery 큐 비우기 오류: {str(e)}")
            return False
    
    def start_celery_worker(self):
        """Celery 워커 시작"""
        try:
            logger.info("Celery 워커 시작 중...")
            # 현재 디렉토리 확인
            current_dir = os.getcwd()
            
            # Celery 워커 명령어
            cmd = [
                "celery", 
                "-A", "core/config", 
                "worker", 
                "--loglevel=info",
                "--concurrency=2",
                "--without-heartbeat",
                "--without-gossip"
            ]
            
            # 워커 프로세스 시작
            self.celery_worker_process = subprocess.Popen(
                cmd,
                cwd=current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # 로그 모니터링 스레드 시작
            celery_log_thread = threading.Thread(
                target=self._monitor_celery_logs,
                args=(self.celery_worker_process,)
            )
            celery_log_thread.daemon = True
            celery_log_thread.start()
            
            # 워커 시작 확인을 위해 잠시 대기
            time.sleep(3)
            
            if self.celery_worker_process.poll() is None:
                # Redis에 상태 저장
                redis_conn = get_redis_connection("default")
                redis_conn.set("cabinet:service:celery", "running", ex=3600)
                redis_conn.set("cabinet:service:celery:pid", str(self.celery_worker_process.pid), ex=3600)
                
                self.services_status['celery'] = True
                logger.info(f"Celery 워커 시작 완료 (PID: {self.celery_worker_process.pid})")
                return True
            else:
                stdout, stderr = self.celery_worker_process.communicate(timeout=1)
                logger.error(f"Celery 워커 시작 실패: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Celery 워커 시작 중 오류: {str(e)}")
            return False
    
    def start_kafka_consumer(self):
        """Kafka 소비자 시작"""
        try:
            logger.info("Kafka 소비자 시작 중...")
            self.kafka_consumer = CabinetRentConsumer()
            self.kafka_consumer.start()
            
            # 시작 확인을 위해 잠시 대기
            time.sleep(2)
            
            # Redis에 상태 저장
            redis_conn = get_redis_connection("default")
            
            if hasattr(self.kafka_consumer, 'is_alive') and self.kafka_consumer.is_alive():
                redis_conn.set("cabinet:service:kafka", "running", ex=3600)
                self.services_status['kafka'] = True
                logger.info("Kafka 소비자 시작 완료")
                return True
            else:
                redis_conn.set("cabinet:service:kafka", "failed", ex=3600)
                logger.warning("Kafka 소비자 시작 상태 확인 불가")
                return False
        except Exception as e:
            logger.error(f"Kafka 소비자 시작 실패: {str(e)}")
            
            # Redis에 상태 저장
            try:
                redis_conn = get_redis_connection("default")
                redis_conn.set("cabinet:service:kafka", "unavailable", ex=3600)
            except:
                pass
                
            return False
    
    def _monitor_celery_logs(self, process):
        """Celery 로그 모니터링"""
        try:
            for line in iter(process.stdout.readline, ''):
                logger.info(f"Celery: {line.strip()}")
                if not self.running:
                    break
        except Exception as e:
            logger.error(f"Celery 로그 모니터링 오류: {str(e)}")
    
    def _monitor_services(self):
        """서비스 상태 모니터링 및 관리"""
        while self.running:
            try:
                # 1. Redis 상태 업데이트
                redis_conn = get_redis_connection("default")
                redis_conn.set("cabinet:service:status", "running", ex=3600)
                
                # 2. Celery 워커 상태 확인 및 필요시 재시작
                if self.services_status['celery'] and self.celery_worker_process:
                    if self.celery_worker_process.poll() is not None:
                        logger.warning("Celery 워커가 종료되었습니다. 재시작 중...")
                        self.start_celery_worker()
                
                # 3. Kafka 소비자 상태 확인 및 필요시 재시작
                if self.services_status['kafka'] and self.kafka_consumer:
                    if not hasattr(self.kafka_consumer, 'is_alive') or not self.kafka_consumer.is_alive():
                        logger.warning("Kafka 소비자가 종료되었습니다. 재시작 중...")
                        self.start_kafka_consumer()
                
                # 4. 스레드 풀 상태 확인
                if self.services_status['thread_pool'] and self.thread_pool:
                    if not self.thread_pool.running:
                        logger.warning("스레드 풀이 중지되었습니다. 재시작 중...")
                        self.start_thread_pool()
                
            except Exception as e:
                logger.error(f"서비스 모니터링 중 오류: {str(e)}")
            
            # 60초마다 확인
            time.sleep(60)