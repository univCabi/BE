from enum import Enum

class CabinetStatusEnum(Enum):
    BROKEN = 'BROKEN'
    AVAILABLE = 'AVAILABLE'
    USING = 'USING'
    OVERDUE = 'OVERDUE'