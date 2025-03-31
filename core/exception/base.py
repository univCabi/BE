class ApplicationError(Exception):
    """애플리케이션 기본 예외 클래스"""
    status_code = 500
    error_code = "application_error"
    
    def __init__(self, message=None, status_code=None, error_code=None, details=None):
        self.message = message or "애플리케이션 오류가 발생했습니다"
        self.status_code = status_code or self.status_code
        self.error_code = error_code or self.error_code
        self.details = details
        super().__init__(self.message)

class ValidationError(ApplicationError):
    """입력값 검증 실패 예외"""
    status_code = 400
    error_code = "validation_error"

class NotFoundError(ApplicationError):
    """리소스를 찾을 수 없는 예외"""
    status_code = 404
    error_code = "not_found"
    
class AuthenticationError(ApplicationError):
    """인증 실패 예외"""
    status_code = 401
    error_code = "authentication_error"

class AuthorizationError(ApplicationError):
    """권한 부족 예외"""
    status_code = 403
    error_code = "authorization_error"

class ConflictError(ApplicationError):
    """자원 충돌 예외"""
    status_code = 409
    error_code = "conflict_error"

class BadRequestError(ApplicationError):
    """잘못된 요청 예외"""
    status_code = 400
    error_code = "bad_request_error"