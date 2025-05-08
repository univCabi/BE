from web3 import Web3
import json
import os
from django.conf import settings
from datetime import datetime

class CabinetBlockchainService:
    def __init__(self):
        # 개발/테스트 모드 확인
        self.dev_mode = getattr(settings, 'BLOCKCHAIN_DEV_MODE', True)
        
        if self.dev_mode:
            # 개발 모드에서는 실제 블록체인에 연결하지 않음
            self.contract_address = "0x0000000000000000000000000000000000000000"
            print("Running in blockchain development mode")
            return
        
        # 실제 모드: 이더리움 노드에 연결
        try:
            self.w3 = Web3(Web3.HTTPProvider(settings.ETHEREUM_NODE_URL))
            
            # 컨트랙트 ABI와 주소 설정
            contract_abi_path = getattr(settings, 'CONTRACT_ABI_PATH', None)
            
            if contract_abi_path and os.path.exists(contract_abi_path):
                with open(contract_abi_path) as f:
                    contract_abi = json.load(f)
            else:
                # ABI 파일이 없는 경우 기본 빈 ABI 사용
                print(f"Contract ABI file not found at {contract_abi_path}. Using empty ABI.")
                contract_abi = []
            
            self.contract_address = settings.CONTRACT_ADDRESS
            self.contract = self.w3.eth.contract(address=self.contract_address, abi=contract_abi)
            
            # 트랜잭션 서명에 사용할 계정 설정
            self.account = self.w3.eth.account.from_key(settings.ETHEREUM_PRIVATE_KEY)
            
        except Exception as e:
            print(f"Error initializing blockchain service: {e}")
            self.dev_mode = True
            self.contract_address = "0x0000000000000000000000000000000000000000"
    
    def mint_cabinet_history_nft(self, cabinet_id, history_id, start_time, expired_at):
        """캐비넷 히스토리 NFT 발행"""
        if self.dev_mode:
            # 개발 모드에서는, 트랜잭션이 성공한 것처럼 로그 출력
            print(f"[DEV MODE] Minted NFT for cabinet {cabinet_id}, history {history_id}")
            return "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
            
        # 기본 이더리움 주소 (실제로는 유저별 주소를 사용하는 것이 좋음)
        user_address = "0x0000000000000000000000000000000000000000"
        
        # Unix timestamp로 변환
        start_timestamp = int(start_time.timestamp())
        expired_timestamp = int(expired_at.timestamp())
        
        # 스마트 컨트랙트 함수 호출하여 NFT 발행
        tx = self.contract.functions.assignCabinet(
            cabinet_id,
            history_id,
            user_address,
            start_timestamp,
            expired_timestamp
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 2000000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        # 트랜잭션 해시 반환
        return tx_hash.hex()