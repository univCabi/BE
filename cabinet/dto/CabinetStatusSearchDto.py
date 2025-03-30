from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class CabinetStatusSearchDto(BaseValidatedSerializer):
    status = serializers.CharField(
        required=True,
        help_text='조회할 사물함 상태 (AVAILABLE, USING, BROKEN, OVERDUE)'
    )
    
    def validate_status(self, value):
        """status가 유효한 상태값인지 검증"""
        valid_statuses = ['AVAILABLE', 'USING', 'BROKEN', 'OVERDUE']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"유효하지 않은 상태입니다. {valid_statuses} 중 하나여야 합니다")
        return value
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance