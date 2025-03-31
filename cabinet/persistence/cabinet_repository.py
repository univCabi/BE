from cabinet.models import cabinets
from django.db.models import Count, Case, When
from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException, CabinetReturnException

from cabinet.persistence.cabinet_history_repository import CabinetHistoryRepository

cabinet_history_repository = CabinetHistoryRepository()

from cabinet.exceptions import CabinetNotFoundException, CabinetAlreadyRentedException, UserHasRentalException

class CabinetRepository:
    def get_cabinets_by_building_id(self, building_id : int):
        cabinet_qs = cabinets.objects.filter(building_id=building_id).select_related('user_id', 'cabinet_positions')

        if not cabinet_qs.exists():
            raise CabinetNotFoundException(building_id=building_id)
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
                raise UserHasRentalException(user_id=user_id)
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
            user_id_id=user_id
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
    
    def change_cabinet_status_by_ids(self, cabinet_ids: list, new_status: str, reason: str):
            """
            특정 ID 목록의 사물함 상태를 변경하고 성공/실패한 캐비닛 정보 반환
            """
            failed_ids = []
            successful_cabinets = []
            
            for cabinet_id in cabinet_ids:
                try:
                    # 먼저 해당 ID의 캐비넷이 존재하는지 확인
                    cabinet = cabinets.objects.get(id=cabinet_id)
                    
                    # 상태 변경
                    updated = self.update_cabinet_status(cabinet_id, None, new_status)
                    
                    if updated:
                        # 업데이트 후 최신 상태의 캐비넷 객체 가져오기
                        updated_cabinet = cabinets.objects.select_related('building_id').get(id=cabinet_id)
                        
                        # 정보를 직접 업데이트하는 대신, 객체를 우선 가져온 다음 시리얼라이저로 넘기기 위해
                        # 별도 처리하지 않고 그대로 추가
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
                except Exception as e:
                    failed_ids.append({
                        'id': cabinet_id, 
                        'reason': f'처리 중 오류 발생: {str(e)}'
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
            raise CabinetNotFoundException(status=status_param)
        
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

