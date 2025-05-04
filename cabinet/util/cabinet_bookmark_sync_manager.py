import traceback
from django.utils import timezone
from cabinet.persistence.cabinet_bookmark_redis_repository import CabinetBookmarkRedisRepository
from cabinet.persistence.cabinet_bookmark_repository import CabinetBookmarkRepository
from cabinet.persistence.cabinet_repository import CabinetRepository
from core.config.redis_lock import RedisLock
from authn.business.authn_service import AuthnService
from cabinet.type import CabinetStatusEnum
import logging
import json

logger = logging.getLogger(__name__)

class BookmarkSyncManager:
    def __init__(self):
        self.redis_repo = CabinetBookmarkRedisRepository()
        self.db_repo = CabinetBookmarkRepository()
        self.cabinet_repo = CabinetRepository()
        self.authn_service = AuthnService()
    
    def is_cabinet_bookmarkable(self, cabinet_info):
        """캐비닛의 상태에 따라 북마크 가능 여부 확인"""
        # BROKEN 상태인 경우 북마크 불가
        if cabinet_info.status == CabinetStatusEnum.BROKEN.value:
            return False
        return True
    
    def sync_to_database(self):
        """Redis의 북마크 변경사항을 데이터베이스에 동기화"""
        # 동기화 작업 시작 로그
        logger.info("북마크 동기화 작업 시작")
        result = {
            "status": "success",
            "processed": 0,
            "skipped": 0,
            "errors": 0
        }
        
        try:
            # Redis 연결 확인 (문제 디버깅을 위해 추가)
            try:
                changed_keys_count = len(self.redis_repo.redis_conn.smembers("cabinet:bookmarks:changed"))
                logger.info(f"Redis 연결 확인: 변경된 북마크 키 수: {changed_keys_count}")
            except Exception as e:
                logger.error(f"Redis 연결 확인 중 오류: {str(e)}")
                result["status"] = "failed"
                result["error"] = f"Redis 연결 오류: {str(e)}"
                return result
            
            # 동기화 작업이 동시에 실행되지 않도록 락 획득
            with RedisLock("bookmark_sync", expire_time=15) as lock:
                if not lock.acquired:
                    logger.warning("북마크 동기화 락 획득 실패, 다른 프로세스가 이미 동기화 중입니다.")
                    result["status"] = "skipped"
                    result["reason"] = "lock_not_acquired"
                    return result
                
                # 변경된 북마크 목록 조회
                try:
                    changed_bookmarks = self.redis_repo.get_changed_bookmarks()
                    logger.info(f"변경된 북마크 조회: {len(changed_bookmarks)}개")
                    
                    # 디버깅: 첫 번째 북마크 데이터 로깅
                    if changed_bookmarks and len(changed_bookmarks) > 0:
                        logger.info(f"첫 번째 북마크 데이터 샘플: {json.dumps(changed_bookmarks[0], default=str)}")
                    
                except Exception as e:
                    logger.error(f"변경된 북마크 조회 중 오류: {str(e)}")
                    result["status"] = "failed"
                    result["error"] = f"북마크 조회 오류: {str(e)}"
                    return result
                
                if not changed_bookmarks:
                    logger.info("동기화할 북마크 변경사항이 없습니다.")
                    return result
                
                logger.info(f"{len(changed_bookmarks)}개의 북마크 변경사항을 동기화합니다.")
                
                processed_keys = []
                skipped_keys = []
                
                for bookmark in changed_bookmarks:
                    try:
                        user_id = bookmark.get('user_id')
                        cabinet_id = bookmark.get('cabinet_id')
                        # 북마크 상태와 캐비닛 상태 구분
                        bookmark_status = bookmark.get('bookmark_status', bookmark.get('status', 'unknown'))
                        cabinet_status = bookmark.get('cabinet_status')
                        
                        logger.info(f"처리 중인 북마크: user_id={user_id}, cabinet_id={cabinet_id}, bookmark_status={bookmark_status}, cabinet_status={cabinet_status}")
                        
                        # cabinet_id가 딕셔너리인 경우 ID 추출
                        if isinstance(cabinet_id, dict):
                            cabinet_id = cabinet_id.get('id')
                        
                        # user_id로 사용자 정보 조회
                        try:
                            from user.models import users
                            
                            # 디버깅: user_id 타입 확인
                            logger.info(f"user_id 타입: {type(user_id)}, 값: {user_id}")
                            
                            user_obj = users.objects.get(id=user_id)
                            logger.info(f"사용자 조회 성공: id={user_id}")
                            
                            user_info = self.authn_service.get_authn_by_user_id(user_obj.id)
                            
                            if not user_info:
                                logger.error(f"사용자 인증 정보를 찾을 수 없습니다: {user_id}")
                                result["errors"] += 1
                                continue
                            
                            cabinet_info = self.cabinet_repo.get_cabinet_by_id(cabinet_id)
                            if not cabinet_info:
                                logger.error(f"캐비닛 정보를 찾을 수 없습니다: {cabinet_id}")
                                result["errors"] += 1
                                continue
                            
                            # 북마크 상태에 따라 DB 업데이트
                            if bookmark_status == 'active':
                                # 캐비닛 상태 확인
                                logger.info(f"캐비닛 상태: {cabinet_info.status}")
                                
                                if not self.is_cabinet_bookmarkable(cabinet_info):
                                    logger.warning(f"캐비닛이 {cabinet_info.status} 상태이므로 북마크를 추가할 수 없습니다: {cabinet_id}")
                                    skipped_keys.append(f"{user_id}:{cabinet_id}")
                                    result["skipped"] += 1
                                    continue
                                
                                # 북마크 추가 수행
                                try:
                                    db_result = self.db_repo.add_bookmark(user_info, cabinet_info)
                                    logger.info(f"북마크 추가 동기화 완료: {user_id}:{cabinet_id}, 결과: {db_result}")
                                    result["processed"] += 1
                                except Exception as e:
                                    logger.error(f"북마크 추가 실패: {user_id}:{cabinet_id} - {str(e)}")
                                    logger.error(traceback.format_exc())  # 스택 트레이스 추가
                                    result["errors"] += 1
                                    continue
                                    
                            elif bookmark_status == 'deleted':
                                # 북마크 삭제는 캐비닛 상태와 관계없이 진행
                                try:
                                    db_result = self.db_repo.remove_bookmark(user_info, cabinet_info)
                                    logger.info(f"북마크 삭제 동기화 완료: {user_id}:{cabinet_id}, 결과: {db_result}")
                                    result["processed"] += 1
                                except Exception as e:
                                    logger.error(f"북마크 삭제 실패: {user_id}:{cabinet_id} - {str(e)}")
                                    logger.error(traceback.format_exc())  # 스택 트레이스 추가
                                    result["errors"] += 1
                                    continue
                            
                            # 처리 완료된 키 추가
                            processed_keys.append(f"{user_id}:{cabinet_id}")
                            
                        except Exception as e:
                            logger.error(f"사용자/캐비닛 정보 조회 중 오류: {str(e)}")
                            logger.error(traceback.format_exc())  # 스택 트레이스 추가
                            result["errors"] += 1
                            continue
                    except Exception as e:
                        logger.error(f"북마크 처리 중 예상치 못한 오류: {str(e)}")
                        logger.error(traceback.format_exc())  # 스택 트레이스 추가
                        result["errors"] += 1
                        continue
                
                # 처리 완료된 북마크 변경 목록에서 제거
                if processed_keys:
                    try:
                        removed_count = self.redis_repo.clear_changed_bookmarks(processed_keys)
                        logger.info(f"{len(processed_keys)}개의 북마크 동기화가 완료되었습니다. (Redis에서 {removed_count}개 제거됨)")
                    except Exception as e:
                        logger.error(f"처리 완료된 북마크 목록 정리 중 오류: {str(e)}")
                        logger.error(traceback.format_exc())  # 스택 트레이스 추가
                        result["status"] = "partial_success"
                
                # 건너뛴 북마크 로그
                if skipped_keys:
                    logger.info(f"{len(skipped_keys)}개의 북마크가 캐비닛 상태로 인해 건너뛰었습니다.")
        
        except Exception as e:
            logger.error(f"북마크 동기화 작업 중 예상치 못한 오류: {str(e)}")
            logger.error(traceback.format_exc())  # 스택 트레이스 추가
            result["status"] = "failed"
            result["error"] = str(e)
        
        logger.info(f"북마크 동기화 작업 종료: {result}")
        return result