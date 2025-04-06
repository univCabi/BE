from rest_framework import serializers
from cabinet.models import cabinets

class CabinetAdminReturnSerializer(serializers.ModelSerializer):
    building = serializers.SerializerMethodField()
    floor = serializers.SerializerMethodField()
    cabinetNumber = serializers.IntegerField(source='cabinet_number')
    brokenDate = serializers.SerializerMethodField()
    userName = serializers.SerializerMethodField()
    
    class Meta:
        model = cabinets
        fields = ['id', 'building', 'floor', 'cabinetNumber', 'status', 
                  'reason', 'brokenDate', 'userName']
    
    def get_building(self, obj):
        return obj.building_id.name if obj.building_id else None
    
    def get_floor(self, obj):
        return obj.building_id.floor if obj.building_id else None
    
    def get_brokenDate(self, obj):
        """BROKEN 상태일 때만 업데이트 날짜를 반환"""
        if obj.status == 'BROKEN':
            return obj.updated_at
        return None
    
    
    def get_userName(self, obj):
        """사용자가 있을 경우 이름 반환"""
        if obj.user_id:
            return obj.user_id.name
        return None
    