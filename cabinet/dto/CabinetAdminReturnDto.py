from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class CabinetAdminReturnDto(BaseValidatedSerializer):
    cabinetIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text='반납할 사물함 ID 목록 (하나의 사물함만 반납하더라도 배열로 전달)'
    )

    def validate_cabinetIds(self, value):
        """cabinetIds가 빈 배열이 아닌지 검증"""
        if not value:  # 빈 배열인 경우
            raise serializers.ValidationError("cabinetIds 배열은 최소 하나 이상의 값을 포함해야 합니다.")
        return value
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance