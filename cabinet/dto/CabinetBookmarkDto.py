from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class CabinetBookmarkDto(BaseValidatedSerializer):
    cabinetId = serializers.IntegerField(
        required=True,
        help_text='사물함 ID'
    )

    def validate_cabinetId(self, value):
        """cabinetId가 양수인지 검증"""
        if value <= 0:
            raise serializers.ValidationError("cabinetId는 양수여야 합니다.")
        return value
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance