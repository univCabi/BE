from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class CabinetSearchDetailDto(BaseValidatedSerializer):
    keyword = serializers.CharField(help_text='검색어')

    def validate_keyword(self, value):
        if value is None:
            raise serializers.ValidationError('검색어를 입력해주세요.')
        elif len(value) == 1 and value.isdigit():
            pass
        elif not isinstance(value, int) and len(value) < 2  :
            raise serializers.ValidationError('검색어는 2글자 이상 입력해주세요.')
        return value
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance