from rest_framework import serializers

class CabinetStatusStatisticsSerializer(serializers.Serializer):
    name = serializers.CharField()
    total = serializers.IntegerField()
    using = serializers.IntegerField()
    overdue = serializers.IntegerField()
    broken = serializers.IntegerField()
    available = serializers.IntegerField()

class CabinetStatisticsSerializer(serializers.Serializer):
    """전체 캐비닛 통계 데이터 시리얼라이저"""
    buildings = CabinetStatusStatisticsSerializer(many=True)