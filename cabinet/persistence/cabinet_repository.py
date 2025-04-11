from django.utils import timezone
from cabinet.models import cabinets
from django.db.models import Count, Case, When
from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException, CabinetReturnException

from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

cabinet_history_repository = CabinetHistoryRepository()

from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException

class CabinetRepository:
    def get_cabinets_by_building_ids(self, building_ids):
        """
        여러 건물 ID를 받아 해당하는 캐비넷 목록을 반환
        """
        cabinet_qs = cabinets.objects.filter(
            building_id__in=building_ids
        ).select_related('user_id', 'cabinet_positions')

        if not cabinet_qs.exists():
            raise CabinetNotFoundException(building_ids=building_ids)
            
        return cabinet_qs
    
    def get_cabinet_by_id(self, cabinet_id : int):
        cabinet = cabinets.objects.filter(id=cabinet_id).select_related('user_id', 'cabinet_positions').first()

        if not cabinet:
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        return cabinet
    
    def check_valid_rental(self, user_id : int, cabinet_id : int):
        # 1. 사용자가 이미 다른 캐비넷을 대여했는지 확인
        try :
            if cabinet_history_repository.get_renting_cabinet_history_by_user_id(user_id) :
                raise UserHasRentalException()
        except CabinetNotFoundException:
            pass

        # 2. 해당 캐비넷이 이미 대여 중인지 확인
        try :
            if cabinet_history_repository.get_renting_cabinet_history_by_cabinet_id(cabinet_id):
                raise CabinetAlreadyRentedException(cabinet_id=cabinet_id)
        except CabinetNotFoundException:
            pass
        
        # 3. 캐비넷이 존재하는지 확인
        cabinet = cabinets.objects.get(id=cabinet_id)
        if not cabinet :
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        return cabinet
    
    def check_valid_return(self, user_id : int, cabinet_id : int):
        # 1. 사용자가 해당 캐비넷을 대여했는지 확인
        if not cabinet_history_repository.get_using_cabinet_info(user_id=user_id, cabinet_id=cabinet_id):
            raise UserHasRentalException(user_id=user_id)
        
        # 2. 캐비넷이 존재하는지 확인
        cabinet = cabinets.objects.get(id=cabinet_id)
        if not cabinet :
            raise CabinetNotFoundException(cabinet_id=cabinet_id)
        return cabinet
        
    def update_cabinet_status(self, cabinet_id : int, user_id : int, status : str):
        return cabinets.objects.filter(id=cabinet_id).update(
            status=status, 
            user_id_id=user_id,
            updated_at=timezone.now()
        )
    
    def get_cabinets_exact_match_by_cabinet_number(self, cabinet_number : int):
        return cabinets.objects.filter(cabinet_number__exact=cabinet_number)
    
    def get_cabinets_contains_by_building_name(self, building_name : str):
        return cabinets.objects.filter(building_id__name__contains=building_name)
    
    def get_all_cabinets(self) :
        return cabinets.objects.all().order_by('id')
    
    def return_cabinets_by_ids(self, cabinet_ids: list):
        """
        특정 ID 목록의 사물함을 반납처리하고 성공/실패한 캐비닛 정보 반환
        """
        failed_ids = []
        successful_cabinets = []
        
        for cabinet_id in cabinet_ids:
            try:
                # 먼저 해당 ID의 캐비닛이 존재하는지 확인
                cabinet = cabinets.objects.get(id=cabinet_id)
                
                # USING 또는 OVERDUE 상태인지 확인
                if cabinet.status not in ['USING', 'OVERDUE'] or not cabinet.user_id:
                    failed_ids.append({
                        'id': cabinet_id,
                        'reason': '반납 가능한 상태(USING 또는 OVERDUE)가 아닙니다'
                    })
                    continue
                    
                # 활성 대여 이력 종료
                cabinet_history_repository.return_cabinet(cabinet, cabinet.user_id)
            
                # 사물함 상태 업데이트
                updated = self.update_cabinet_status(cabinet_id, None, 'AVAILABLE')
                
                if updated:
                    # 업데이트 후 최신 상태의 캐비닛 객체 가져오기
                    updated_cabinet = cabinets.objects.select_related('building_id').get(id=cabinet_id)
                    successful_cabinets.append(updated_cabinet)
                else:
                    failed_ids.append({
                        'id': cabinet_id, 
                        'reason': '업데이트 실패'
                    })
                    
            except cabinets.DoesNotExist:
                failed_ids.append({
                    'id': cabinet_id, 
                    'reason': '해당 ID의 사물함이 존재하지 않습니다'
                })
        
        return successful_cabinets, failed_ids
    
    def change_cabinet_status_by_ids(self, cabinet_ids, new_status, reason=''):
        """
        관리자용: 여러 사물함의 상태를 변경합니다.
        
        Args:
            cabinet_ids: 상태를 변경할 사물함 ID 목록
            new_status: 변경할 상태 (AVAILABLE, BROKEN)
            reason: 상태 변경 사유 (BROKEN 상태일 때 필수)
            
        Returns:
            successful_cabinets: 성공적으로 상태가 변경된 사물함 목록
            failed_ids: 상태 변경에 실패한 사물함 ID와 실패 사유
        """
        successful_cabinets = []
        failed_ids = []
        
        for cabinet_id in cabinet_ids:
            try:
                # 사물함 조회
                cabinet = cabinets.objects.filter(id=cabinet_id).first()
                
                if not cabinet:
                    failed_ids.append({
                        "id": cabinet_id,
                        "reason": "사물함을 찾을 수 없습니다."
                    })
                    continue
                
                # 상태 변경
                cabinet.status = new_status
                
                # BROKEN 상태일 때는 사유 필드 업데이트
                if new_status == "BROKEN":
                    cabinet.reason = reason
                elif new_status == "AVAILABLE":
                    # AVAILABLE 상태로 변경 시 사용자 정보 초기화 및 관련 히스토리 종료
                    if cabinet.user_id:
                        # 사용 중인 사물함 히스토리 종료
                        #history = cabinet_histories.objects.filter(
                        #    cabinet_id=cabinet,
                        #    ended_at__isnull=True
                        #).first()
                        
                        #if history:
                        #    history.ended_at = timezone.now()
                        #    history.save()
                        cabinet_history_repository.return_cabinet(cabinet, cabinet.user_id)
                    
                    # 사용자 정보 초기화
                    cabinet.user_id = None
                    cabinet.reason = None
                
                cabinet.save()
                successful_cabinets.append(cabinet)
                
            except Exception as e:
                failed_ids.append({
                    "id": cabinet_id,
                    "reason": str(e)
                })
        
        return successful_cabinets, failed_ids
    
    def assign_cabinet_to_user(self, cabinet_id, user_auth_info, status="USING"):
        """
        관리자용: 사물함을 특정 사용자에게 할당합니다.
        
        Args:
            cabinet_id: 할당할 사물함 ID
            user_auth_info: 사용자 인증 정보 객체
            status: 변경할 상태 (USING 또는 OVERDUE)
            
        Returns:
            successful_cabinets: 성공적으로 할당된 사물함
            failed_ids: 할당 실패 정보
        """
        successful_cabinets = []
        failed_ids = []
        
        try:
            # 사물함 조회
            cabinet = cabinets.objects.filter(id=cabinet_id).first()
            
            if not cabinet:
                failed_ids.append({
                    "id": cabinet_id,
                    "reason": "사물함을 찾을 수 없습니다."
                })
                return successful_cabinets, failed_ids
            
            user = user_auth_info.user_id
            
            # 사물함 상태 업데이트
            cabinet.user_id = user
            cabinet.status = status
            cabinet.save()

            # 상태에 따라 적절한 사물함 히스토리 생성
            if status == "OVERDUE":
                # OVERDUE 상태일 경우 현재 시간을 기준으로 ended_at과 expired_at 설정
                cabinet_history_repository.rent_cabinet_overdue(cabinet, user)
            else:
                # 일반적인 대여 시에는 기존 메소드 사용
                cabinet_history_repository.rent_cabinet(cabinet, user)
            
            successful_cabinets.append(cabinet)
            
        except Exception as e:
            failed_ids.append({
                "id": cabinet_id,
                "reason": str(e)
            })
        
        return successful_cabinets, failed_ids
    
    def get_cabinet_statistics(self):
        """
        건물별 사물함 상태 통계를 가져옵니다.
        """
        building_stats = cabinets.objects.select_related('building_id').values(
            'building_id__name'
        ).annotate(
            total=Count('id'),
            using=Count(Case(When(status='USING', then=1))),
            available=Count(Case(When(status='AVAILABLE', then=1))),
            broken=Count(Case(When(status='BROKEN', then=1))),
            overdue=Count(Case(When(status='OVERDUE', then=1)))
        ).order_by('building_id__name')
        
        result = []
        for stat in building_stats:
            result.append({
                'name': stat['building_id__name'] or '미지정',
                'total': stat['total'],
                'using': stat['using'],
                'overdue': stat['overdue'],
                'broken': stat['broken'],
                'available': stat['available']  # 'AVAILABLE' 상태는 'returned'와 동일
            })
        
        return result
    
    def get_cabinets_by_status(self, status_param):
        """
        특정 상태의 사물함 목록을 조회합니다.
        """
        # 해당 상태의 모든 사물함 조회
        cabinets_qs = cabinets.objects.filter(
            status=status_param
        ).select_related('building_id', 'user_id')
        
        if not cabinets_qs.exists():
            raise CabinetNotFoundException()
        
        results = []
        for cabinet in cabinets_qs:
            cabinet_data = {
                'id': cabinet.id,
                'building': cabinet.building_id.name if cabinet.building_id else None,
                'floor': cabinet.building_id.floor if cabinet.building_id else None,
                'section': cabinet.building_id.section if hasattr(cabinet.building_id, 'section') else None,
                'position': {
                    'x': cabinet.cabinet_positions.cabinet_x_pos,
                    'y': cabinet.cabinet_positions.cabinet_y_pos
                } if hasattr(cabinet, 'cabinet_positions') and cabinet.cabinet_positions else None,
                'cabinetNumber': cabinet.cabinet_number,
                'status': cabinet.status,
                'reason': cabinet.reason,
                'user': None,
            }
            
            # 사용자 정보 추가 (사용중인 경우)
            if cabinet.user_id:
                user = cabinet.user_id
                cabinet_data['user'] = {
                    'studentNumber': user.student_number if hasattr(user, 'student_number') else None,
                    'name': user.name if hasattr(user, 'name') else None
                }
                
                # 연체된 경우 대여 시작일, 만료일 추가
                if status_param == 'OVERDUE':
                    #rental_history = cabinet_histories.objects.filter(
                    #    cabinet_id=cabinet,
                    #    ended_at=None
                    #).first()

                    rental_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
                    
                    if rental_history:
                        cabinet_data['rentalStartDate'] = rental_history.created_at
                        cabinet_data['overDate'] = rental_history.expired_at
                elif status_param == "BROKEN":
                    # select_related를 사용하여 관련 객체까지 함께 로드
                    rental_history = cabinet_history_repository.get_cabinet_histories_by_cabinet_id(cabinet.id)
                    
                    if rental_history:
                        cabinet_data['rentalStartDate'] = rental_history.created_at
                        cabinet_data['brokenDate'] = rental_history.cabinet_id.updated_at
            results.append(cabinet_data)
        
        return results

