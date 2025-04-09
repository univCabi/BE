from rest_framework import serializers

class CabinetBookmarkSerializer(serializers.ModelSerializer):
    """
    북마크 시리얼라이저 - 북마크 ID와 북마크한 캐비넷 정보를 모두 포함
    북마크 관리(삭제)에 필요한 정보도 함께 제공
    """
    isBookmark = serializers.SerializerMethodField()

    def get_isBookmark(self, obj):
        return True
    