from core.exception.base import NotFoundError, ConflictError, BadRequestError

class UserNotFoundException(NotFoundError):
    """사용자를 찾을 수 없는 예외"""
    error_code = "user_not_found"
    
    def __init__(self, student_number=None):
        detail = f" (학번: {student_number})" if student_number else ""
        super().__init__(f"사용자를 찾을 수 없습니다{detail}")