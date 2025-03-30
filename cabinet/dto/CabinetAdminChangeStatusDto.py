from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class CabinetAdminChangeStatusDto(BaseValidatedSerializer):
    cabinetIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text='반납할 사물함 ID 목록 (하나의 사물함만 반납하더라도 배열로 전달)'
    )
    newStatus = serializers.CharField(
        required=True,
        help_text='변경할 사물함 상태 (AVAILABLE, USING, BROKEN, OVERDUE)'
    )
    reason = serializers.CharField(
        required=False,
        help_text='사물함 상태 변경 사유'
    )

    def validate_cabinetIds(self, value):
        """cabinetIds가 빈 배열이 아닌지 검증"""
        if not value:  # 빈 배열인 경우
            raise serializers.ValidationError("cabinetIds 배열은 최소 하나 이상의 값을 포함해야 합니다.")
        return value
    
    def validate_newStatus(self, value):
        """newStatus가 유효한 상태값인지 검증"""
        if value not in ['AVAILABLE', 'USING', 'BROKEN', 'OVERDUE']:
            raise serializers.ValidationError("newStatus는 AVAILABLE, USING, BROKEN, OVERDUE 중 하나여야 합니다.")
        return value
    
    def validate(self, data):
        """
        1. cabinetIds와 newStatus가 동시에 존재하는지 검증
        2. newStatus가 BROKEN인 경우 reason 필드가 필수인지 검증
        """
        # cabinetIds와 newStatus가 동시에 존재하는지 검증
        if not ('cabinetIds' in data and 'newStatus' in data):
            raise serializers.ValidationError("cabinetIds와 newStatus는 동시에 존재해야 합니다.")
        
        # newStatus가 BROKEN인 경우 reason 필드가 필수인지 검증
        if data['newStatus'] == 'BROKEN':
            if not data.get('reason'):
                raise serializers.ValidationError("사물함 상태를 'BROKEN'으로 변경할 때는 reason 필드가 필수입니다.")
    
        return data
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance