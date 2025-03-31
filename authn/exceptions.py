from core.exception.base import AuthenticationError, NotFoundError

class InvalidCredentialsError(AuthenticationError):
    """잘못된 인증 정보 예외"""
    error_code = "invalid_credentials"
    
    def __init__(self, message=None):
        super().__init__(message or "아이디 또는 비밀번호가 올바르지 않습니다")

class UserNotFoundError(NotFoundError):
    """사용자를 찾을 수 없는 예외"""
    error_code = "user_not_found"
    
    def __init__(self, student_number=None):
        detail = f" (학번: {student_number})" if student_number else ""
        super().__init__(f"사용자를 찾을 수 없습니다{detail}")