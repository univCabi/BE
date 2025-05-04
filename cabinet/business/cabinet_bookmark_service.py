
from authn.business.authn_service import AuthnService
from cabinet.exceptions import CabinetBookmarkAlreadyExistsException, CabinetNotFoundException
from cabinet.persistence.cabinet_bookmark_redis_repository import CabinetBookmarkRedisRepository
from cabinet.persistence.cabinet_bookmark_repository import CabinetBookmarkRepository
from cabinet.persistence.cabinet_repository import CabinetRepository
from user.exceptions import UserNotFoundException

authn_service = AuthnService()

cabinet_bookmark_repository = CabinetBookmarkRepository()
cabinet_repository = CabinetRepository()

cabinet_bookmark_redis_repository = CabinetBookmarkRedisRepository()

class CabinetBookmarkService :
    def add_bookmark(self, cabinet_id, student_number):
        # 사용자 정보 조회

        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number=student_number)
        
        cabinet_info = cabinet_repository.get_cabinet_by_id(cabinet_id) 

        if not cabinet_info:
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        
        # Redis에서 북마크 존재 여부 확인
        bookmark_exists = cabinet_bookmark_redis_repository.get_existing_active_bookmark(
            user_info=user_auth_info,
            cabinet_info=cabinet_info
        )
        
        if bookmark_exists:
            raise CabinetBookmarkAlreadyExistsException(cabinet_id=cabinet_info.id)

        bookmark_data = cabinet_bookmark_redis_repository.add_bookmark(
            user_info=user_auth_info,
            cabinet_info=cabinet_info
        )
        
        return bookmark_data
    
    def remove_bookmark(self, cabinet_id, student_number):

        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number=student_number)
        
        cabinet_info = cabinet_repository.get_cabinet_by_id(cabinet_id) 

        if not cabinet_info:
            raise CabinetNotFoundException(cabinet_id=cabinet_id)

        # Redis에서 북마크 존재 여부 확인
        bookmark_exists = cabinet_bookmark_redis_repository.get_existing_active_bookmark(
            user_info=user_auth_info,
            cabinet_info=cabinet_info
        )
        
        if not bookmark_exists:
            from cabinet.exceptions import CabinetBookmarkNotFoundException
            raise CabinetBookmarkNotFoundException(cabinet_id=cabinet_info.id)
        
        # Redis에서 북마크 삭제
        redis_result = cabinet_bookmark_redis_repository.remove_bookmark(
            user_info=user_auth_info,
            cabinet_info=cabinet_info
        )
        
        # 추가: DB에서도 동기화하여 삭제 (즉시 처리)
        try:
            cabinet_bookmark_repository.remove_bookmark(
                user_info=user_auth_info,
                cabinet_info=cabinet_info
            )
        except Exception as e:
            # DB 삭제 실패 시에도 Redis 삭제 결과는 반환
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"DB 북마크 삭제 실패: {e}")
        
        return redis_result
    
    def get_bookmarks(self, student_number):
        # 사용자 정보 조회
        user_auth_info = authn_service.get_authn_by_student_number(student_number)

        if not user_auth_info:
            raise UserNotFoundException(student_number=student_number)
        
        # Redis에서 북마크 목록 조회
        bookmarks = cabinet_bookmark_redis_repository.get_bookmarks(user_info=user_auth_info)
        
        # Redis에 데이터가 없으면 DB에서 조회하고 Redis에 캐싱
        if not bookmarks:
            db_bookmarks = cabinet_bookmark_repository.get_bookmarks(user_info=user_auth_info)
            
            # DB 데이터를 Redis에 캐싱 (북마크 상태 유효성 검사 추가)
            if db_bookmarks:
                for bookmark in db_bookmarks:
                    # 삭제된 북마크인지 확인 (deleted_at이 null이 아닌 경우 건너뜀)
                    if hasattr(bookmark, 'deleted_at') and bookmark.deleted_at is not None:
                        continue
                    
                    cabinet_info = bookmark.cabinet_id
                    
                    cabinet_bookmark_redis_repository.add_bookmark(
                        user_info=user_auth_info,
                        cabinet_info=cabinet_info
                    )
                
                # 다시 Redis에서 조회
                bookmarks = cabinet_bookmark_redis_repository.get_bookmarks(user_info=user_auth_info)
        
        return bookmarks