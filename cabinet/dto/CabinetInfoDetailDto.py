from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException


#TODO: escape 처리
class CabinetInfoDetailDto(BaseValidatedSerializer):
    cabinetId = serializers.IntegerField(help_text='사물함 ID', min_value=1)

    def validate_cabinetId(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('사물함 ID는 숫자로 입력해주세요.')
        return value

    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance
