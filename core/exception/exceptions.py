from core.exception.base import NotFoundError, ConflictError, ValidationError

class GlobalDtoValidationException(ValidationError):
    """Global DTO 검증 실패 예외"""
    error_code = "global_dto_validation_error"
    
    def __init__(self, details):
        super().__init__("요청 파라미터를 확인해주세요", details=details)

class GlobalRedisLockException(ConflictError):
    """Redis Lock 예외"""
    error_code = "redis_lock_error"
    
    def __init__(self, details):
        super().__init__("Redis Lock을 획득하지 못했습니다", details=details)