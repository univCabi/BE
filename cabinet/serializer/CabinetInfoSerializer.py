from rest_framework import serializers
from cabinet.models import cabinets
from django.utils import timezone
import datetime

class CabinetInfoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    isVisible = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    isMine = serializers.SerializerMethodField()
    cabinetXPos = serializers.IntegerField(source='cabinet_positions.cabinet_x_pos', read_only=True)
    cabinetYPos = serializers.IntegerField(source='cabinet_positions.cabinet_y_pos', read_only=True)
    cabinetNumber = serializers.IntegerField(source='cabinet_number', read_only=True)
    isRentAvailable = serializers.SerializerMethodField()
    isFree = serializers.SerializerMethodField()
    class Meta:
        model = cabinets
        fields = ['id', 'cabinetNumber', 'cabinetXPos', 'cabinetYPos', 'status', 'isVisible', 'username', 'isMine', 'isRentAvailable', 'isFree']

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

        
        # 기본 조건: 상태가 'AVAILABLE'이고 payable이 'FREE'여야 함
        if obj.status != 'AVAILABLE' or obj.payable != 'FREE':
            return False
        
        try:
            # 날짜 비교만 수행하여 시간대 문제 회피
            # (1) 현재 시간
            current_time = timezone.now()
            
            # (2) 마지막 업데이트 시간에서 날짜 부분만 추출
            updated_date = obj.updated_at.date()
            
            # (3) 다음 날 계산
            next_day = updated_date + datetime.timedelta(days=1)
            
            # (4) 현재 날짜
            current_date = current_time.date()
            
            # (5) 현재 시간이 다음 날보다 이후인 경우 무조건 대여 가능
            if current_date > next_day:
                return True
            
            # (6) 현재 날짜가 다음 날과 같고, 시간이 13시 이후인 경우 대여 가능
            if current_date == next_day and current_time.hour >= 13:
                return True
            
            # 그 외의 경우 대여 불가능
            return False
            
        except Exception as e:
            # 오류 발생 시 로그 기록 후 대여 불가능 반환
            print(f"Error in get_isRentAvailable: {str(e)}")
            return False
        
    def get_isFree(self, obj):
       return obj.payable == 'FREE'