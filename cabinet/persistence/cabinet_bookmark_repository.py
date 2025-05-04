from cabinet.exceptions import CabinetBookmarkAlreadyExistsException, CabinetBookmarkNotFoundException
from cabinet.models import cabinet_bookmarks

from django.utils import timezone

class CabinetBookmarkRepository:

    def get_existing_active_bookmark(self, user_info, cabinet_info):
        # 활성화된 북마크가 있는지 확인
        print(f"get_existing_active_bookmark: {user_info.user_id}, {cabinet_info}")
        return cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            deleted_at__isnull=True
        ).first()
    
    def get_deleted_bookmark(self, user_info, cabinet_info):
        # 삭제된 북마크가 있는지 확인
        return cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            deleted_at__isnull=False
        ).first()
    
    def create_bookmark(self, user_info, cabinet_info):
        # 북마크 생성
        bookmark = cabinet_bookmarks.objects.create(
            user_id=user_info.user_id,
            cabinet_id=cabinet_info,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        if bookmark is None:
            raise CabinetBookmarkNotFoundException(cabinet_id=cabinet_info.id)
        return bookmark

    def add_bookmark(self, user_info, cabinet_info):
        # 삭제된 북마크가 있는지 확인
        deleted_bookmark = self.get_deleted_bookmark(user_info, cabinet_info)
        
        if deleted_bookmark:
            # 케이스 2: 이미 삭제된 북마크가 있는 경우 - 복구
            deleted_bookmark.deleted_at = None
            deleted_bookmark.updated_at = timezone.now()
            deleted_bookmark.save(update_fields=['deleted_at', 'updated_at'])
            return deleted_bookmark, False
        
        # 케이스 1: 최초 생성
        bookmark = self.create_bookmark(user_info, cabinet_info)
        
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
        return cabinet_bookmarks.objects.filter(
            user_id=user_info.user_id,
            deleted_at__isnull=True
        ).select_related('cabinet_id', 'cabinet_id__building_id')