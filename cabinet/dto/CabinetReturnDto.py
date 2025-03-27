from rest_framework import serializers

class CabinetReturnDto(serializers.Serializer):
    cabinetId = serializers.IntegerField(help_text='사물함 ID', min_value=1)

    def validate_cabinetId(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('사물함 ID는 숫자로 입력해주세요.')
        return value
    
