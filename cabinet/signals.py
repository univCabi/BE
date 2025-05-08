from django.db.models.signals import post_save
from django.dispatch import receiver
from cabinet.models import cabinet_histories
from cabinet.business.cabinet_blockchain_service import CabinetBlockchainService
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

@receiver(post_save, sender=cabinet_histories)
def create_blockchain_record(sender, instance, created, **kwargs):
    """캐비넷 히스토리 생성 시 블록체인에 기록"""
    
    # 새로 생성된 레코드인 경우에만 처리
    if created:
        try:
            service = CabinetBlockchainService()
            
            # 블록체인에 NFT 발행
            tx_hash = service.mint_cabinet_history_nft(
                cabinet_id=instance.cabinet_id.id,
                history_id=instance.id,
                start_time=instance.created_at,
                expired_at=instance.expired_at
            )
            
            # 로그 기록
            logger.info(f"Cabinet history #{instance.id} recorded on blockchain: {tx_hash}")
            
        except Exception as e:
            # 오류 발생 시 로그 기록
            logger.error(f"Failed to record cabinet history #{instance.id} on blockchain: {e}")