from django.apps import AppConfig
import os
import threading
import logging

logger = logging.getLogger(__name__)

# 전역 변수로 async_service_manager 참조 유지
async_service_manager = None

# 메인 스레드에서 실행될 신호 핸들러
def handle_signal(signum, frame):
    global async_service_manager
    logger.info(f"시그널 {signum} 수신: 서비스 종료 중...")
    if async_service_manager:
        async_service_manager.stop_all()

class CabinetConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cabinet'

    def ready(self):
        # Start the thread pool when Django starts
        # Only in main process (not in forked processes like Celery workers)
        import os
        if os.environ.get('RUN_MAIN', None) != 'true':
            from cabinet.util.cabinet_async_service_manager import AsyncServiceManager
            
            # 별도 스레드에서 비동기 서비스 시작
            def start_services():
                try:
                    global async_service_manager
                    from cabinet.util.cabinet_async_service_manager import AsyncServiceManager
                    async_service_manager = AsyncServiceManager()
                    # Celery와 Kafka 모두 건너뛰기
                    async_service_manager.start_all(skip_celery=True, skip_kafka=True)
                    logger.info("비동기 서비스 관리자가 시작되었습니다.")
                except Exception as e:
                    logger.error(f"비동기 서비스 시작 실패: {str(e)}")
            
            # 스레드 시작
            service_thread = threading.Thread(target=start_services)
            service_thread.daemon = True  # 메인 스레드 종료 시 함께 종료되도록 설정
            service_thread.start()
            logger.info("비동기 서비스 스레드가 시작되었습니다.")