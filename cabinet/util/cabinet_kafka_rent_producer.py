import time
from kafka import KafkaProducer
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CabinetRentProducer:
    def __init__(self):
        logger.debug("Starting the Kafka producer")
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                # 연결 타임아웃 설정
                connections_max_idle_ms=5000,
                request_timeout_ms=5000,
                # 재시도 횟수 제한
                retries=2
            )
            self.available = True
            logger.info("Kafka 프로듀서 초기화 성공")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            self.available = False

    def send_rental_request(self, cabinet_id, student_number):
        """Send a cabinet rental request to Kafka"""
        if not self.available:
            logger.warning(f"Kafka producer not available, skipping message for cabinet {cabinet_id}")
            return False
            
        try:
            logger.debug(f"Sending rental request for cabinet {cabinet_id} by student {student_number}")
            self.producer.send(
                settings.KAFKA_CABINET_RENTAL_TOPIC,
                {
                    'cabinet_id': cabinet_id,
                    'student_number': student_number,
                    'timestamp': str(time.time()),
                    'action': 'rent'
                }
            )
            self.producer.flush(timeout=5)
            logger.debug(f"메시지 전송 성공 (사물함 ID: {cabinet_id})")
            return True
        except Exception as e:
            logger.error(f"Failed to send Kafka message: {str(e)}")
            return False
    
    def send_return_request(self, cabinet_id, student_number):
        """Kafka로 사물함 반납 요청 메시지 전송"""
        if not self.available:
            logger.warning(f"Kafka 프로듀서 사용 불가, 메시지 전송 건너뜀 (사물함 ID: {cabinet_id})")
            return False
            
        try:
            logger.debug(f"사물함 반납 요청 메시지 전송 중 (ID: {cabinet_id}, 학번: {student_number})")
            self.producer.send(
                settings.KAFKA_CABINET_RENTAL_TOPIC,
                {
                    'cabinet_id': cabinet_id,
                    'student_number': student_number,
                    'timestamp': str(time.time()),
                    'action': 'return'
                }
            )
            self.producer.flush(timeout=5)
            logger.debug(f"메시지 전송 성공 (사물함 ID: {cabinet_id})")
            return True
        except Exception as e:
            logger.error(f"Kafka 메시지 전송 실패: {str(e)}")
            return False