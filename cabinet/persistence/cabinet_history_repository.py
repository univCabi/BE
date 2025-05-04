from django.utils import timezone

from cabinet.models import cabinet_histories

from cabinet.exceptions import CabinetNotFoundException, CabinetRentFailedException, CabinetReturnFailedException

class CabinetHistoryRepository:
    def check_already_rented(self, user_id : int):
        return cabinet_histories.objects.filter(user_id=user_id, ended_at=None).exists()
    
    def get_renting_cabinet_history_by_user_id(self, user_id : int):
        return cabinet_histories.objects.filter(user_id=user_id, ended_at=None).first()

    def get_renting_cabinet_history_by_cabinet_id(self, cabinet_id : int):
        return cabinet_histories.objects.filter(cabinet_id=cabinet_id, ended_at=None).first()

    def get_using_cabinet_info(self, user_id : int, cabinet_id : int):
        return cabinet_histories.objects.filter(user_id=user_id, cabinet_id=cabinet_id, ended_at=None).first()
        
    
    def rent_cabinet(self, cabinet : object, user_id : int):
        result = cabinet_histories.objects.update_or_create(
            user_id=user_id,
            cabinet_id=cabinet,
            defaults={
                'expired_at': timezone.now() + timezone.timedelta(days=120),
                'ended_at': None,
                'created_at': timezone.now(),
                'updated_at': timezone.now()
            }
        )

        if not result:
            raise CabinetNotFoundException()
        return result
        
    def return_cabinet(self, cabinet : object, user_id : int):
        result = cabinet_histories.objects.update_or_create(
            user_id=user_id,
            cabinet_id=cabinet,
            ended_at=None,
            defaults={
                'expired_at': timezone.now(),
                'ended_at': timezone.now(), 
                'updated_at': timezone.now()
            }
        )

        if not result:
            raise CabinetReturnFailedException(cabinet_id=cabinet.id)
        return result
    
    def get_cabinet_histories_by_user_id(self, user_id : int):
        return cabinet_histories.objects.filter(user_id=user_id).order_by(
            'ended_at'
        ).extra(select={'ended_at_null': 'ended_at IS NULL'}, order_by=['-ended_at_null', '-ended_at'])

    
    def get_cabinet_histories_by_cabinet_id(self, cabinet_id : int):
        return cabinet_histories.objects.select_related('cabinet_id').filter(
            cabinet_id=cabinet_id,
            ended_at=None
        ).first()
    
    def rent_cabinet_overdue(self, cabinet : object, user_id : int):
        result =  cabinet_histories.objects.create(
            user_id=user_id,
            cabinet_id=cabinet,
            expired_at=timezone.now(),
            ended_at=timezone.now()
        )

        if not result:
            raise CabinetNotFoundException()
        return result
    