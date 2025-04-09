from rest_framework import serializers

from cabinet.models import cabinet_bookmarks

class CabinetBookmarkListSerializer(serializers.ModelSerializer):
    """
    북마크 시리얼라이저 - 북마크 ID와 북마크한 캐비넷 정보를 모두 포함
    북마크 관리(삭제)에 필요한 정보도 함께 제공
    """
    id = serializers.IntegerField(source='cabinet_id.id')
    building = serializers.CharField(source='cabinet_id.building_id.name')
    floor = serializers.IntegerField(source='cabinet_id.building_id.floor')
    cabinetNumber = serializers.IntegerField(source='cabinet_id.cabinet_number')
    status = serializers.CharField(source='cabinet_id.status')
    createdAt = serializers.DateTimeField(source='created_at')
    
    class Meta:
        model = cabinet_bookmarks
        fields = ['id', 'building', 'floor', 'cabinetNumber', 'status', 'createdAt']