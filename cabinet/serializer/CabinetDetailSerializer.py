from rest_framework import serializers

from cabinet.models import cabinets, cabinet_histories

from authn.models import authns

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
