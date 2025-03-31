from rest_framework import serializers

class CabinetAdminReturnSerializer(serializers.Serializer):
    building = serializers.CharField(source='building_id.name')
    floor = serializers.IntegerField(source='building_id.floor')
    cabinetNumber = serializers.IntegerField(source='cabinet_number')
    status = serializers.CharField()