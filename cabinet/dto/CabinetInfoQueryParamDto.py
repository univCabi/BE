from rest_framework import serializers
from core.validate.base import BaseValidatedSerializer

from building.models import BuildingNameEnum

from core.exception.exceptions import GlobalDtoValidationException

class CabinetInfoQueryParamDto(BaseValidatedSerializer):
    building = serializers.CharField(help_text='건물명')
    floor = serializers.IntegerField(help_text='층수', min_value=1)

    def validate_building(self, value):
        try:
            # BuildingNameEnum(value)를 통해 유효한지 확인
            BuildingNameEnum(value)
        except ValueError:
            raise serializers.ValidationError('유효하지 않은 건물명입니다.')
        return value


    def validate_floor(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('층수는 숫자로 입력해주세요.')
        return value
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance