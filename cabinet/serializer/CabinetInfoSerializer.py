from rest_framework import serializers
from cabinet.models import cabinets

class CabinetInfoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    isVisible = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    isMine = serializers.SerializerMethodField()
    cabinetXPos = serializers.IntegerField(source='cabinet_positions.cabinet_x_pos', read_only=True)
    cabinetYPos = serializers.IntegerField(source='cabinet_positions.cabinet_y_pos', read_only=True)
    cabinetNumber = serializers.IntegerField(source='cabinet_number', read_only=True)
    isRentAvailable = serializers.SerializerMethodField()

    class Meta:
        model = cabinets
        fields = ['id', 'cabinetNumber', 'cabinetXPos', 'cabinetYPos', 'status', 'isVisible', 'username', 'isMine', 'isRentAvailable']

    def get_isVisible(self, obj):
        return obj.user_id.is_visible if obj.user_id else False

    def get_username(self, obj):
        return obj.user_id.name if obj.user_id else None

    #TODO: Implement this method
    def get_isMine(self, obj):
        request = self.context.get('request')
        # request가 None인 경우 처리
        if not request:
            return False
            
        user_id = cabinets.objects.filter(id=obj.id).values('user_id').first().get('user_id')
        return user_id is not None and user_id == request.user.id if user_id else False
    
    def get_isRentAvailable(self, obj):
        from django.utils import timezone
        import datetime
        
        # 기본 조건: 상태가 'AVAILABLE'이고 payable이 'FREE'여야 함
        if obj.status != 'AVAILABLE' or obj.payable != 'FREE':
            return False
        
        # 캐비닛이 업데이트된 시간 확인
        last_updated = obj.updated_at
        current_time = timezone.now()
        
        # 다음 날 13시 계산
        next_day = last_updated + datetime.timedelta(days=1)
        next_day_13 = datetime.datetime.combine(
            next_day.date(), 
            datetime.time(13, 0),
            tzinfo=timezone.get_current_timezone()
        )
        
        # 현재 시간이 다음 날 13시 이후인지 확인
        return current_time >= next_day_13