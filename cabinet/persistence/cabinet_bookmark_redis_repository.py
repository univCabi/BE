from django.utils import timezone
from django_redis import get_redis_connection
import json
from datetime import timedelta
import logging
from cabinet.type import CabinetStatusEnum

logger = logging.getLogger(__name__)

class CabinetBookmarkRedisRepository:
    def __init__(self):
        self.redis_conn = get_redis_connection("default")
        self.bookmark_key_prefix = "cabinet:bookmark:"
        self.user_bookmarks_key_prefix = "cabinet:user_bookmarks:"
        # 12시간 = 43200초
        self.ttl = 43200  

    def _get_bookmark_key(self, user_id, cabinet_id):
        """개별 북마크의 키 생성"""
        # ID가 객체일 수 있으므로 문자열로 변환
        user_id = str(user_id)
        cabinet_id = str(cabinet_id)
        return f"{self.bookmark_key_prefix}{user_id}:{cabinet_id}"
    
    def _get_user_bookmarks_key(self, user_id):
        """사용자별 북마크 목록 키 생성"""
        user_id = str(user_id)
        return f"{self.user_bookmarks_key_prefix}{user_id}"
    
    def get_existing_active_bookmark(self, user_info, cabinet_info):
        """활성화된 북마크가 있는지 확인"""
        try:
            # user_id 추출
            if hasattr(user_info, 'user_id'):
                if hasattr(user_info.user_id, 'id'):
                    user_id = user_info.user_id.id
                else:
                    user_id = user_info.user_id
            else:
                user_id = user_info.id
            
            cabinet_id = cabinet_info.id
            
            bookmark_key = self._get_bookmark_key(user_id, cabinet_id)
            bookmark_data_json = self.redis_conn.get(bookmark_key)
            
            if not bookmark_data_json:
                return None
            
            bookmark_data = json.loads(bookmark_data_json)
            if bookmark_data.get('bookmark_status') == 'active':
                return bookmark_data
            return None
        except Exception as e:
            logger.error(f"북마크 확인 중 오류 발생: {str(e)}")
            return None
    
    def add_bookmark(self, user_info, cabinet_info):
        """Redis에 북마크 추가"""
        try:
            # user_id 추출
            if hasattr(user_info, 'user_id'):
                if hasattr(user_info.user_id, 'id'):
                    user_id = user_info.user_id.id
                else:
                    user_id = user_info.user_id
            else:
                user_id = user_info.id
                
            cabinet_id = cabinet_info.id
            
            # 캐비닛 상태 확인 - BROKEN 상태인 경우 북마크 불가
            cabinet_status = getattr(cabinet_info, 'status', None)
            if cabinet_status == CabinetStatusEnum.BROKEN.value:
                logger.warning(f"캐비닛이 BROKEN 상태이므로 북마크 추가 불가: user_id={user_id}, cabinet_id={cabinet_id}")
                return None
            
            logger.info(f"북마크 추가 시작: user_id={user_id}, cabinet_id={cabinet_id}, cabinet_status={cabinet_status}")
            
            # 캐비닛 정보 추출 - 시리얼라이저에 필요한 형식으로 저장
            cabinet_data = {}
            try:
                cabinet_data = {
                    'id': cabinet_info.id,
                    'cabinet_number': getattr(cabinet_info, 'cabinet_number', None),
                    'status': cabinet_status  # 실제 캐비닛 상태 저장
                }
                
                # building_id 정보 추출
                if hasattr(cabinet_info, 'building_id'):
                    building = cabinet_info.building_id
                    if building:
                        cabinet_data['building'] = {
                            'id': getattr(building, 'id', None),
                            'name': getattr(building, 'name', None),
                            'floor': getattr(building, 'floor', None)
                        }
            except Exception as e:
                logger.warning(f"캐비닛 데이터 추출 중 오류: {str(e)}")
                cabinet_data = {
                    'id': cabinet_id,
                    'status': cabinet_status
                }
            
            bookmark_key = self._get_bookmark_key(user_id, cabinet_id)
            user_bookmarks_key = self._get_user_bookmarks_key(user_id)
            
            # 북마크 데이터 설정
            bookmark_data = {
                'id': cabinet_id,
                'user_id': user_id,
                'cabinet_id': cabinet_data,
                'bookmark_status': 'active',  # 북마크 상태는 'active'
                'cabinet_status': cabinet_status,  # 캐비닛 상태는 실제 캐비닛 상태
                'created_at': timezone.now().isoformat(),
                'updated_at': timezone.now().isoformat(),
                'deleted_at': None
            }
            
            # JSON으로 직렬화
            try:
                bookmark_json = json.dumps(bookmark_data)
                logger.info(f"북마크 데이터 직렬화 성공: {bookmark_key}")
            except TypeError as e:
                logger.error(f"북마크 직렬화 오류: {str(e)}")
                # 간소화된 데이터 저장
                simplified_data = {
                    'id': cabinet_id,
                    'user_id': user_id,
                    'cabinet_id': {'id': cabinet_id, 'status': cabinet_status},
                    'bookmark_status': 'active',
                    'cabinet_status': cabinet_status,
                    'created_at': timezone.now().isoformat(),
                    'updated_at': timezone.now().isoformat(),
                    'deleted_at': None
                }
                bookmark_json = json.dumps(simplified_data)
                bookmark_data = simplified_data
            
            # 파이프라인으로 여러 명령 한번에 실행
            pipeline = self.redis_conn.pipeline()
            
            try:
                pipeline.set(bookmark_key, bookmark_json, ex=self.ttl)
                pipeline.sadd(user_bookmarks_key, str(cabinet_id))
                pipeline.expire(user_bookmarks_key, self.ttl)
                pipeline.sadd("cabinet:bookmarks:changed", f"{user_id}:{cabinet_id}")
                pipeline.execute()
                logger.info(f"북마크 Redis에 저장 성공: {bookmark_key}")
            except Exception as e:
                logger.error(f"Redis 저장 오류: {str(e)}")
                return None
            
            return bookmark_data
            
        except Exception as e:
            logger.error(f"북마크 추가 중 예상치 못한 오류: {str(e)}")
            return None
    
    def remove_bookmark(self, user_info, cabinet_info):
        """Redis에서 북마크 상태를 deleted로 변경"""
        try:
            # user_id 추출
            if hasattr(user_info, 'user_id'):
                if hasattr(user_info.user_id, 'id'):
                    user_id = user_info.user_id.id
                else:
                    user_id = user_info.user_id
            else:
                user_id = user_info.id
                
            cabinet_id = cabinet_info.id
            cabinet_status = getattr(cabinet_info, 'status', None)
            
            logger.info(f"북마크 삭제 시작: user_id={user_id}, cabinet_id={cabinet_id}, cabinet_status={cabinet_status}")
            
            bookmark_key = self._get_bookmark_key(user_id, cabinet_id)
            user_bookmarks_key = self._get_user_bookmarks_key(user_id)
            
            # 현재 저장된 북마크 정보 조회
            bookmark_data_json = self.redis_conn.get(bookmark_key)
            if not bookmark_data_json:
                logger.warning(f"삭제할 북마크를 찾을 수 없음: {bookmark_key}")
                return None
            
            bookmark_data = json.loads(bookmark_data_json)
            bookmark_data['bookmark_status'] = 'deleted'  # 북마크 상태만 'deleted'로 변경
            bookmark_data['cabinet_status'] = cabinet_status  # 캐비닛 상태 업데이트
            bookmark_data['deleted_at'] = timezone.now().isoformat()
            bookmark_data['updated_at'] = timezone.now().isoformat()
            
            # 파이프라인으로 여러 명령 한번에 실행
            pipeline = self.redis_conn.pipeline()
            pipeline.set(bookmark_key, json.dumps(bookmark_data), ex=self.ttl)
            pipeline.srem(user_bookmarks_key, str(cabinet_id))
            pipeline.sadd("cabinet:bookmarks:changed", f"{user_id}:{cabinet_id}")
            # 중요: user_bookmarks_key가 비어있게 되면 키 자체를 삭제
            pipeline.scard(user_bookmarks_key)  # 남은 항목 수 확인
            result = pipeline.execute()
            
            remaining_items = result[-1]  # scard 결과
            if remaining_items == 0:
                # 북마크가 없으면 키 자체를 삭제
                self.redis_conn.delete(user_bookmarks_key)
                logger.info(f"북마크가 모두 삭제되어 키 제거: {user_bookmarks_key}")
            
            logger.info(f"북마크 삭제 완료: {bookmark_key}")
            return bookmark_data
            
        except Exception as e:
            logger.error(f"북마크 삭제 중 예상치 못한 오류: {str(e)}")
            return None
    
    def get_bookmarks(self, user_info=None):
        """사용자의 북마크 목록 조회"""
        try:
            # user_id 추출
            if hasattr(user_info, 'user_id'):
                if hasattr(user_info.user_id, 'id'):
                    user_id = user_info.user_id.id
                else:
                    user_id = user_info.user_id
            else:
                user_id = user_info.id
            
            logger.info(f"북마크 목록 조회 시작: user_id={user_id}")
            
            user_bookmarks_key = self._get_user_bookmarks_key(user_id)
            
            # 사용자의 북마크 캐비닛 ID 목록 조회
            cabinet_ids = self.redis_conn.smembers(user_bookmarks_key)
            logger.info(f"사용자({user_id})의 북마크 수: {len(cabinet_ids)}")
            
            # 시리얼라이저에 필요한 형식으로 변환된 북마크 객체들
            transformed_bookmarks = []
            
            # 각 북마크의 상세 정보 조회
            for cabinet_id in cabinet_ids:
                cabinet_id = cabinet_id.decode() if isinstance(cabinet_id, bytes) else cabinet_id
                bookmark_key = self._get_bookmark_key(user_id, cabinet_id)
                bookmark_data_json = self.redis_conn.get(bookmark_key)
                
                if bookmark_data_json:
                    bookmark_data = json.loads(bookmark_data_json)
                    # 북마크 상태가 active인 것만 포함
                    if bookmark_data.get('bookmark_status') == 'active':
                        # BROKEN 상태의 캐비닛은 포함하지 않음
                        cabinet_status = bookmark_data.get('cabinet_status')
                        if cabinet_status != CabinetStatusEnum.BROKEN.value:
                            # 시리얼라이저에 맞는 객체 형태로 변환
                            bookmark_obj = self._transform_to_serializable_format(bookmark_data)
                            transformed_bookmarks.append(bookmark_obj)
            
            logger.info(f"변환된 북마크 객체 수: {len(transformed_bookmarks)}")
            return transformed_bookmarks
            
        except Exception as e:
            logger.error(f"북마크 목록 조회 중 예상치 못한 오류: {str(e)}")
            return []
    
    def _transform_to_serializable_format(self, bookmark_data):
        """Redis 데이터를 시리얼라이저가 기대하는 형식으로 변환"""
        # 기본 객체 생성
        bookmark_obj = type('CabinetBookmarkObj', (), {})()
        
        # 필수 속성 설정
        bookmark_obj.id = bookmark_data.get('id')
        bookmark_obj.created_at = bookmark_data.get('created_at')
        bookmark_obj.updated_at = bookmark_data.get('updated_at')
        
        # cabinet_id 객체 생성
        cabinet_obj = type('CabinetObj', (), {})()
        cabinet_data = bookmark_data.get('cabinet_id', {})
        
        if isinstance(cabinet_data, dict):
            # 딕셔너리인 경우 (복잡한 정보가 저장된 경우)
            cabinet_obj.id = cabinet_data.get('id')
            cabinet_obj.cabinet_number = cabinet_data.get('cabinet_number')
            cabinet_obj.status = cabinet_data.get('status')  # 캐비닛의 실제 상태
            
            # building_id 객체 생성
            building_obj = type('BuildingObj', (), {})()
            building_data = cabinet_data.get('building', {})
            
            if isinstance(building_data, dict):
                building_obj.id = building_data.get('id')
                building_obj.name = building_data.get('name')
                building_obj.floor = building_data.get('floor')
            else:
                # 기본값 설정
                building_obj.id = None
                building_obj.name = None
                building_obj.floor = None
            
            cabinet_obj.building_id = building_obj
        else:
            # 간단한 정보만 저장된 경우 (cabinet_id가 정수인 경우)
            cabinet_obj.id = cabinet_data
            cabinet_obj.cabinet_number = None
            # 캐비닛 상태 설정 (bookmark_data에서 직접 가져옴)
            cabinet_obj.status = bookmark_data.get('cabinet_status')
            
            building_obj = type('BuildingObj', (), {})()
            building_obj.id = None
            building_obj.name = None
            building_obj.floor = None
            cabinet_obj.building_id = building_obj
        
        # 북마크 객체에 캐비닛 객체 연결
        bookmark_obj.cabinet_id = cabinet_obj
        
        return bookmark_obj
    
    def get_changed_bookmarks(self):
        """변경된 북마크 목록 조회 (DB 동기화용)"""
        try:
            changed_keys = self.redis_conn.smembers("cabinet:bookmarks:changed")
            logger.info(f"변경된 북마크 키 수: {len(changed_keys)}")
            
            changed_bookmarks = []
            
            for key in changed_keys:
                key = key.decode() if isinstance(key, bytes) else key
                user_id, cabinet_id = key.split(':')
                bookmark_key = self._get_bookmark_key(user_id, cabinet_id)
                bookmark_data_json = self.redis_conn.get(bookmark_key)
                
                if bookmark_data_json:
                    bookmark_data = json.loads(bookmark_data_json)
                    changed_bookmarks.append(bookmark_data)
                else:
                    logger.warning(f"변경 목록에는 있지만 데이터를 찾을 수 없음: {key}")
            
            return changed_bookmarks
            
        except Exception as e:
            logger.error(f"변경된 북마크 목록 조회 중 예상치 못한 오류: {str(e)}")
            return []
    
    def clear_changed_bookmarks(self, processed_keys):
        """처리 완료된 북마크를 변경 목록에서 제거"""
        if not processed_keys:
            return 0
            
        try:
            result = self.redis_conn.srem("cabinet:bookmarks:changed", *processed_keys)
            logger.info(f"처리 완료된 북마크 {len(processed_keys)}개 중 {result}개가 변경 목록에서 제거됨")
            return result
        except Exception as e:
            logger.error(f"처리 완료된 북마크 목록 제거 중 오류: {str(e)}")
            return 0
