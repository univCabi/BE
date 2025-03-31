from rest_framework import serializers
from cabinet.serializer.CabinetInfoSerializer import CabinetInfoSerializer

class CabinetFloorSerializer(serializers.Serializer):
    floor = serializers.IntegerField()
    section = serializers.CharField()
    floorWidth = serializers.IntegerField()
    floorHeight = serializers.IntegerField()
    cabinets = CabinetInfoSerializer(many=True)
    
    def __init__(self, building=None, cabinets=None, *args, **kwargs):
        """두 객체를 직접 받는 초기화 메서드"""
        # 데이터를 가공하여 instance 생성
        if building and cabinets is not None:
            instance = {
                'floor': building.floor,
                'section': building.section,
                'floorWidth': building.width,
                'floorHeight': building.height,
                'cabinets': cabinets
            }
            # instance를 사용하여 부모 초기화 호출
            super().__init__(instance, *args, **kwargs)
        else:
            # 기존 초기화 호출 (instance는 None으로 설정)
            super().__init__(None, *args, **kwargs)