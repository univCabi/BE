from rest_framework import serializers

from .models import cabinets, cabinet_positions, cabinet_histories
from authn.models import authns
from univ_cabi.utils import CamelCaseSerializer

class CabinetInfoSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    isVisible = serializers.SerializerMethodField()
    username = serializers.SerializerMethodField()
    isMine = serializers.SerializerMethodField()
    cabinetXPos = serializers.IntegerField(source='cabinet_positions.cabinet_x_pos', read_only=True)
    cabinetYPos = serializers.IntegerField(source='cabinet_positions.cabinet_y_pos', read_only=True)
    cabinetNumber = serializers.IntegerField(source='cabinet_number', read_only=True)

    class Meta:
        model = cabinets
        fields = ['id', 'cabinetNumber', 'cabinetXPos', 'cabinetYPos', 'status', 'isVisible', 'username', 'isMine']

    def get_isVisible(self, obj):
        return obj.user_id.is_visible if obj.user_id else False

    def get_username(self, obj):
        return obj.user_id.name if obj.user_id else None

    def get_isMine(self, obj):
        request = self.context.get('request')
        return obj.user_id == request.user if obj.user_id else False

    
class CabinetFloorSerializer(serializers.Serializer):
    floor = serializers.IntegerField()
    section = serializers.CharField()
    floorWidth = serializers.IntegerField()
    floorHeight = serializers.IntegerField()
    cabinets = CabinetInfoSerializer(many=True)

    def get_cabinets(self, obj):
        cabinets = obj['cabinets']
        return CabinetFloorSerializer(cabinets, many=True, context=self.context).data

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
            'expiredAt'
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


class CabinetHistorySerializer(CamelCaseSerializer):
    building = serializers.CharField(source='cabinet_id.building_id.name', help_text='건물 이름')
    floor = serializers.IntegerField(source='cabinet_id.building_id.floor', help_text='층')
    section = serializers.CharField(source='cabinet_id.building_id.section', help_text='섹션')
    cabinetNumber = serializers.IntegerField(source='cabinet_id.cabinet_number', help_text='캐비넷 번호')
    startDate = serializers.DateTimeField(source='created_at', help_text='사용 시작일', required=False, allow_null=True)
    endDate = serializers.DateTimeField(source='ended_at', help_text='사용 종료일', required=False, allow_null=True)

    class Meta:
        model = cabinet_histories
        fields = ['building', 'floor', 'section', 'cabinetNumber', 'startDate', 'endDate']

        
class CabinetSearchSerializer(serializers.Serializer):
    keyword = serializers.CharField(required=True, max_length=100)



