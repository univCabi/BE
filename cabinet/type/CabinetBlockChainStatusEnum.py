from enum import Enum

class CabinetBlockChainStatusEnum(Enum):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    FAILED = 'FAILED'