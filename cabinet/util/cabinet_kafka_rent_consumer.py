import json
import threading
import logging
from django.conf import settings
from kafka import KafkaConsumer
from core.config.redis_lock import RedisLock

logger = logging.getLogger(__name__)

class CabinetRentConsumer(threading.Thread):
    """Kafka 사물함 대여/반납 메시지 소비자"""
    
    def __init__(self):
        super().__init__(daemon=True)
        self.running = False
        self.setup_consumer()
        
    def setup_consumer(self):
        """Kafka 소비자 초기화"""
        try:
            logger.info("Kafka 소비자 초기화 중")
            self.consumer = KafkaConsumer(
                settings.KAFKA_CABINET_RENTAL_TOPIC,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                group_id='cabinet-rental-group',
                auto_offset_reset='earliest'
            )
            logger.info("Kafka 소비자 초기화 성공")
        except Exception as e:
            logger.error(f"Kafka 소비자 초기화 실패: {str(e)}")
            self.consumer = None

    def process_message(self, message):
        """메시지 처리"""
        try:
            data = message.value
            cabinet_id = data.get('cabinet_id')
            student_number = data.get('student_number')
            action = data.get('action', 'rent')

            logger.info(f"메시지 수신: {action} (사물함 ID: {cabinet_id}, 학번: {student_number})")

            if action == 'rent':
                self._process_rental(cabinet_id, student_number)
            elif action == 'return':
                self._process_return(cabinet_id, student_number)
            else:
                logger.warning(f"알 수 없는 작업: {action}")
        except Exception as e:
            logger.error(f"메시지 처리 중 오류: {str(e)}")

    def _process_rental(self, cabinet_id, student_number):
        """대여 요청 처리"""
        lock_name = f"cabinet:{cabinet_id}:rent"
        with RedisLock(lock_name, expire_time=30) as lock:
            if lock.acquired:
                try:
                    # 순환 참조 방지를 위한 지연 임포트
                    from cabinet.business.cabinet_service import CabinetService
                    cabinet_service = CabinetService()
                    cabinet_service.rent_cabinet(cabinet_id, student_number)
                    logger.info(f"사물함 {cabinet_id} 대여 성공 (학번: {student_number})")
                except Exception as e:
                    logger.error(f"사물함 {cabinet_id} 대여 실패: {str(e)}")
    
    def _process_return(self, cabinet_id, student_number):
        """반납 요청 처리"""
        lock_name = f"cabinet:{cabinet_id}:return"
        with RedisLock(lock_name, expire_time=10) as lock:
            if lock.acquired:
                try:
                    # 순환 참조 방지를 위한 지연 임포트
                    from cabinet.business.cabinet_service import CabinetService
                    cabinet_service = CabinetService()
                    cabinet_service.return_cabinet(cabinet_id, student_number)
                    logger.info(f"사물함 {cabinet_id} 반납 성공 (학번: {student_number})")
                except Exception as e:
                    logger.error(f"사물함 {cabinet_id} 반납 실패: {str(e)}")

    def run(self):
        """소비자 실행"""
        if not self.consumer:
            logger.error("Kafka 소비자가 초기화되지 않아 실행할 수 없습니다")
            return
            
        self.running = True
        logger.info("Kafka 소비자 시작")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                self.process_message(message)
        except Exception as e:
            logger.error(f"Kafka 소비자 실행 중 오류: {str(e)}")
        finally:
            self.running = False
            logger.info("Kafka 소비자 종료")

    def start(self):
        """소비자 스레드 시작"""
        if self.consumer and not self.running:
            super().start()
            logger.info("Kafka 소비자 스레드 시작됨")
        else:
            logger.warning("Kafka 소비자를 시작할 수 없습니다")

    def stop(self):
        """소비자 중지"""
        logger.info("Kafka 소비자 중지 중")
        self.running = False
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka 소비자 연결 종료")