from rest_framework import serializers

from cabinet.models import cabinets

class CabinetAdminReturnSerializer(serializers.ModelSerializer):
    building = serializers.SerializerMethodField()
    floor = serializers.SerializerMethodField()
    cabinetNumber = serializers.SerializerMethodField()  # SerializerMethodField로 변경
    brokenDate = serializers.DateTimeField(required=False, allow_null=True)
    
    class Meta:
        model = cabinets
        fields = ['id', 'building', 'floor', 'cabinetNumber', 'status', 'reason', 'brokenDate']
    
    def get_building(self, obj):
        return obj.building_id.name if obj.building_id else None
    
    def get_floor(self, obj):
        return obj.building_id.floor if obj.building_id else None
    
    def get_cabinetNumber(self, obj):
        # cabinets 모델에 있는 실제 필드명에 따라 이 부분을 수정해야 합니다
        # 예: number, cabinet_number, code 등의 필드일 수 있습니다
        return obj.number if hasattr(obj, 'number') else obj.cabinet_number if hasattr(obj, 'cabinet_number') else None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        
        if instance.status == 'BROKEN':
            data['brokenDate'] = instance.updated_at
        else:
            data['brokenDate'] = None
            
        return data