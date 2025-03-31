
from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class UserProfileUpdateDto(BaseValidatedSerializer):
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')

    def validate_isVisible(self, value):
        if value is None:
            raise serializers.ValidationError('이름 공개 여부를 입력해주세요.')
        return value
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance
