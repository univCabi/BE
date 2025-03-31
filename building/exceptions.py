from core.exception.base import NotFoundError

class BuildingNotFoundException(NotFoundError):
    """건물을 찾을 수 없는 예외"""
    error_code = "building_not_found"
    
    def __init__(self, building=None, floor=None):
        detail = f" (건물: {building}, 층: {floor})" if building else ""
        super().__init__(f"건물을 찾을 수 없습니다{detail}")