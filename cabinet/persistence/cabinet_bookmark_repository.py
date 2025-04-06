from cabinet.exceptions import CabinetBookmarkAlreadyExistsException, CabinetBookmarkNotFoundException
from cabinet.models import cabinet_bookmarks

from django.utils import timezone

class CabinetBookmarkRepository:
    def add_bookmark(self, user_info, cabinet_info):
        # 먼저 이미 활성화된 북마크가 있는지 확인
        existing_active_bookmark = cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            deleted_at__isnull=True
        ).first()
        
        if existing_active_bookmark:
            # 케이스 3: 이미 활성화된 북마크가 있는 경우
            raise CabinetBookmarkAlreadyExistsException(cabinet_id=cabinet_info.id)
        
        # 삭제된 북마크가 있는지 확인
        deleted_bookmark = cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            deleted_at__isnull=False
        ).first()
        
        if deleted_bookmark:
            # 케이스 2: 이미 삭제된 북마크가 있는 경우 - 복구
            deleted_bookmark.deleted_at = None
            deleted_bookmark.updated_at = timezone.now()
            deleted_bookmark.save(update_fields=['deleted_at', 'updated_at'])
            return deleted_bookmark, False
        
        # 케이스 1: 최초 생성
        bookmark = cabinet_bookmarks.objects.create(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )
        
        return bookmark
    
    def remove_bookmark(self, user_info, cabinet_info):
        # 북마크 삭제
        bookmark = cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            deleted_at__isnull=True
        ).first()

        if bookmark:
            bookmark.deleted_at = timezone.now()
            bookmark.save()
            return None
        else:
            raise CabinetBookmarkNotFoundException(cabinet_id=cabinet_info.id)
        
    
    def get_bookmarks(self, user_info):
        bookmarks = cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            deleted_at__isnull=True
        ).select_related('cabinet_id', 'cabinet_id__building_id')
        
        return bookmarks