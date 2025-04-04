from rest_framework import serializers

from django.utils import timezone
import datetime

from cabinet.models import cabinets, cabinet_histories

from authn.models import authns

class CabinetDetailSerializer(serializers.ModelSerializer):
    # Direct fields from related Building model
    floor = serializers.IntegerField(source='building_id.floor')
    section = serializers.CharField(source='building_id.section')
    building = serializers.CharField(source='building_id.name')
    
    # Renamed fields from Cabinets model
    cabinetNumber = serializers.IntegerField(source='cabinet_number')
    status = serializers.CharField()
    
    # Custom fields
    isVisible = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    isMine = serializers.SerializerMethodField()
    isRentAvailable = serializers.SerializerMethodField()
    expiredAt = serializers.SerializerMethodField()

    class Meta:
        model = cabinets
        fields = [
            'floor',
            'section',
            'building',
            'cabinetNumber',
            'status',
            'isVisible',
            'username',
            'isMine',
            'expiredAt',
            'isRentAvailable'
        ]

    def get_isVisible(self, obj):
        """
        Determines if the cabinet is visible based on the associated user's visibility.
        """
        user = obj.user_id
        return user.is_visible if user else False

    def get_username(self, obj):
        """
        Retrieves the username if the user is visible; otherwise, returns None.
        """
        user = obj.user_id
        if user and user.is_visible:
            return user.name
        return None

    def get_isMine(self, obj):
        """
        Determines if the cabinet belongs to the requesting user.
        """
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        student_number = request.user.student_number
        auth_info = authns.objects.filter(user_id=obj.user_id).first()
        if auth_info:
            return student_number == auth_info.student_number
        return False
    
    def get_expiredAt(self, obj):
        """
        Retrieves the expiration date of the cabinet.
        """
        history = cabinet_histories.objects.filter(cabinet_id=obj).first()
        return history.expired_at if history else None

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