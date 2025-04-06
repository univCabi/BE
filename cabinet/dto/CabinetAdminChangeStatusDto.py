from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer
from core.exception.exceptions import GlobalDtoValidationException

class CabinetAdminChangeStatusDto(BaseValidatedSerializer):
    cabinetIds = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        help_text='변경할 사물함 ID 목록 (USING, OVERDUE 상태는 하나만 가능)'
    )
    newStatus = serializers.CharField(
        required=True,
        help_text='변경할 사물함 상태 (AVAILABLE, USING, BROKEN, OVERDUE)'
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        default=None,  # 기본값 설정
        help_text='사물함 상태 변경 사유 (BROKEN 상태일 때 필수)'
    )
    studentNumber = serializers.CharField(
        required=False,
        allow_blank=True,
        default=None,  # 기본값 설정
        help_text='학생 학번 (USING, OVERDUE 상태일 때 필수)'
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
        각 상태에 따른 필수 필드 및 조건 검증:
        1. AVAILABLE: 별다른 조건 없음
        2. USING: studentNumber 필수, cabinetIds는 하나의 값만 가능
        3. BROKEN: reason 필수
        4. OVERDUE: studentNumber 필수, cabinetIds는 하나의 값만 가능
        """
        # cabinetIds와 newStatus가 동시에 존재하는지 검증 (공통)
        if not ('cabinetIds' in data and 'newStatus' in data):
            raise serializers.ValidationError("cabinetIds와 newStatus는 필수 항목입니다.")
        
        # 상태별 조건 검증
        if data['newStatus'] == 'USING' or data['newStatus'] == 'OVERDUE':
            # studentNumber 필수 체크
            if not data.get('studentNumber'):
                raise serializers.ValidationError(f"사물함 상태를 '{data['newStatus']}'으로 변경할 때는 studentNumber 필드가 필수입니다.")
            
            # cabinetIds에는 하나의 ID만 가능
            if len(data['cabinetIds']) > 1:
                raise serializers.ValidationError(f"사물함 상태를 '{data['newStatus']}'으로 변경할 때는 하나의 사물함만 선택할 수 있습니다.")
        
        elif data['newStatus'] == 'BROKEN':
            # reason 필수 체크
            if not data.get('reason'):
                raise serializers.ValidationError("사물함 상태를 'BROKEN'으로 변경할 때는 reason 필드가 필수입니다.")
        
        # AVAILABLE 상태는 추가 검증 없음
        # reason 값이 명시적으로 None이 되도록 설정
        if data['newStatus'] == 'AVAILABLE':
            data['reason'] = None
        
        return data
    
    def to_internal_value(self, data):
        """
        입력 데이터를 내부 표현으로 변환하고, 누락된 필드에 기본값 설정
        """
        # 일반적인 변환 수행
        validated_data = super().to_internal_value(data)
        
        # newStatus가 AVAILABLE인 경우 reason을 None으로 설정
        if validated_data.get('newStatus') == 'AVAILABLE':
            validated_data['reason'] = None
            
        return validated_data
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance