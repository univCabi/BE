from django.core.management.base import BaseCommand
import time
import sys
from cabinet.util.cabinet_async_service_manager import AsyncServiceManager

class Command(BaseCommand):
    help = '캐비넷 비동기 처리 서비스 (스레드 풀, Celery, Kafka) 시작'

    def add_arguments(self, parser):
        parser.add_argument(
            '--skip-celery',
            action='store_true',
            help='Celery 워커 시작 건너뛰기',
        )
        parser.add_argument(
            '--skip-kafka',
            action='store_true',
            help='Kafka 소비자 시작 건너뛰기',
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='시작 전 Celery 큐 비우기',
        )
        parser.add_argument(
            '--background',
            action='store_true',
            help='백그라운드로 실행 (명령 즉시 종료)',
        )

    def handle(self, *args, **options):
        skip_celery = options.get('skip_celery', False)
        skip_kafka = options.get('skip_kafka', False)
        purge = options.get('purge', False)
        background = options.get('background', False)
        
        # 서비스 관리자 생성 및 시작
        service_manager = AsyncServiceManager()
        
        self.stdout.write(self.style.SUCCESS('비동기 서비스 시작 중...'))
        
        # 비동기 서비스 시작
        success = service_manager.start_all(
            skip_celery=skip_celery,
            skip_kafka=skip_kafka,
            purge=purge
        )
        
        if success:
            self.stdout.write(self.style.SUCCESS('비동기 서비스가 성공적으로 시작되었습니다.'))
        else:
            self.stdout.write(self.style.ERROR('비동기 서비스 시작 중 오류가 발생했습니다.'))
            sys.exit(1)
        
        # 백그라운드 모드가 아닌 경우 프로세스 유지
        if not background:
            self.stdout.write(self.style.SUCCESS('서비스가 실행 중입니다. 종료하려면 Ctrl+C를 누르세요.'))
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING('사용자에 의해 중단되었습니다.'))
                service_manager.stop_all()