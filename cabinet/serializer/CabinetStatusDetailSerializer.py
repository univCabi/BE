from rest_framework import serializers

class CabinetUserSerializer(serializers.Serializer):
    """캐비닛 사용자 정보 시리얼라이저"""
    studentNumber = serializers.CharField(allow_null=True)
    name = serializers.CharField(allow_null=True)

class CabinetPositionSerializer(serializers.Serializer):
    """캐비닛 위치 정보 시리얼라이저"""
    x = serializers.IntegerField()
    y = serializers.IntegerField()

class CabinetStatusDetailSerializer(serializers.Serializer):
    """캐비닛 상태 상세 정보 시리얼라이저"""
    id = serializers.IntegerField()
    building = serializers.CharField(allow_null=True)
    floor = serializers.IntegerField(allow_null=True)
    section = serializers.CharField(allow_null=True)
    position = CabinetPositionSerializer(allow_null=True)
    cabinetNumber = serializers.CharField()
    status = serializers.CharField()
    reason = serializers.CharField(allow_null=True)
    user = CabinetUserSerializer(allow_null=True)
    rentalStartDate = serializers.DateTimeField(allow_null=True, required=False)
    overDate = serializers.DateTimeField(allow_null=True, required=False)
    brokenDate = serializers.DateTimeField(allow_null=True, required=False)