from rest_framework import serializers
from cabinet.models import cabinets

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

    #TODO: Implement this method
    def get_isMine(self, obj):
        request = self.context.get('request')
        user_id = cabinets.objects.filter(id=obj.id).values('user_id').first().get('user_id')

        print("user_id: ", user_id)
        print("request.user.id: ", request.user.id)

        return user_id == request.user.id if user_id else False