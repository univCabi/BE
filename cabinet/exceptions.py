from core.exception.base import NotFoundError, ConflictError, BadRequestError

class CabinetNotFoundException(NotFoundError):
    """사물함을 찾을 수 없는 예외"""
    error_code = "cabinet_not_found"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"사물함을 찾을 수 없습니다{detail}")

class CabinetAlreadyRentedException(ConflictError):
    """이미 대여된 사물함 예외"""
    error_code = "cabinet_already_rented"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"이미 대여 중인 사물함입니다{detail}")

class UserHasRentalException(ConflictError):
    """사용자가 이미 다른 사물함을 대여 중인 예외"""
    error_code = "user_has_rental"
    
    def __init__(self, student_number=None):
        detail = f" (학번: {student_number})" if student_number else ""
        super().__init__(f"이미 다른 사물함을 대여 중입니다{detail}")


class CabinetReturnException(BadRequestError):
    """사물함 반납을 실패한 예외"""
    error_code = "cabinet_return_failed"
    
    def __init__(self, failed_ids):
        self.failed_ids = failed_ids
        detail = f" (ID: {failed_ids})" if failed_ids else ""
        super().__init__(f"사물함 반납에 실패했습니다{detail}")


class CabinetBookmarkAlreadyExistsException(ConflictError):
    """북마크가 이미 존재하는 예외"""
    error_code = "cabinet_bookmark_already_exists"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"이미 북마크가 존재합니다{detail}")
class CabinetBookmarkNotFoundException(NotFoundError):
    """북마크를 찾을 수 없는 예외"""
    error_code = "cabinet_bookmark_not_found"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"북마크를 찾을 수 없습니다{detail}")

class CabinetStatusUpdateException(BadRequestError):
    """사물함 상태 업데이트를 실패한 예외"""
    error_code = "cabinet_status_update_failed"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"사물함 상태 업데이트에 실패했습니다{detail}")


class CabinetRentFailedException(BadRequestError):
    """사물함 대여를 실패한 예외"""
    error_code = "cabinet_rent_failed"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"사물함 대여에 실패했습니다{detail}")


class CabinetReturnFailedException(BadRequestError):
    """사물함 반납을 실패한 예외"""
    error_code = "cabinet_return_failed"
    
    def __init__(self, cabinet_id=None):
        detail = f" (ID: {cabinet_id})" if cabinet_id else ""
        super().__init__(f"사물함 반납에 실패했습니다{detail}")