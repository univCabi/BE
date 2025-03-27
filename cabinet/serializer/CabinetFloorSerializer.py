from rest_framework import serializers

from cabinet.serializer.CabinetInfoSerializer import CabinetInfoSerializer


class CabinetFloorSerializer(serializers.Serializer):
    floor = serializers.IntegerField()
    section = serializers.CharField()
    floorWidth = serializers.IntegerField()
    floorHeight = serializers.IntegerField()
    cabinets = CabinetInfoSerializer(many=True)

    def get_cabinets(self, obj):
        cabinets = obj['cabinets']
        return CabinetFloorSerializer(cabinets, many=True, context=self.context).data