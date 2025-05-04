from django.core.management.base import BaseCommand
from cabinet.util.cabinet_bookmark_sync_manager import BookmarkSyncManager
from django.contrib.auth import get_user_model
from django_redis import get_redis_connection
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Redis에 저장된 북마크를 DB에 동기화합니다.'

    def handle(self, *args, **options):
        self.stdout.write('북마크 동기화 시작...')
        
        # Redis 직접 확인
        try:
            redis_conn = get_redis_connection("default")
            changed_keys = redis_conn.smembers("cabinet:bookmarks:changed")
            
            self.stdout.write(f'Redis 변경된 북마크 키: {len(changed_keys)}개')
            
            # 변경된 북마크 정보 출력
            for key in changed_keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                self.stdout.write(f'변경된 북마크 키: {key_str}')
                
                # 키에서 user_id와 cabinet_id 추출
                try:
                    user_id, cabinet_id = key_str.split(':')
                    bookmark_key = f"cabinet:bookmark:{key_str}"
                    bookmark_data = redis_conn.get(bookmark_key)
                    
                    if bookmark_data:
                        bookmark_json = json.loads(bookmark_data)
                        self.stdout.write(f'북마크 데이터: {json.dumps(bookmark_json, indent=2)}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'북마크 데이터 조회 실패: {str(e)}'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Redis 연결 테스트 실패: {str(e)}'))
        
        # 북마크 동기화 실행
        sync_manager = BookmarkSyncManager()
        result = sync_manager.sync_to_database()
        
        if result["status"] == "success":
            self.stdout.write(self.style.SUCCESS(
                f'북마크 동기화가 완료되었습니다. 처리된 항목: {result.get("processed", 0)}, 건너뛴 항목: {result.get("skipped", 0)}'
            ))
        else:
            self.stdout.write(self.style.ERROR(
                f'북마크 동기화 실패: {result.get("error", "알 수 없는 오류")}'
            ))
            