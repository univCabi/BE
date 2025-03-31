from rest_framework import serializers
from core.validate.base import BaseValidatedSerializer

from building.models import BuildingNameEnum

from core.exception.exceptions import GlobalDtoValidationException

class CabinetInfoQueryParamDto(BaseValidatedSerializer):
    building = serializers.CharField(help_text='건물명')
    floors = serializers.CharField(help_text='층수 (쉼표로 구분된 여러 층 지원, 예: 1,2,3)', required=True)

    def validate_building(self, value):
        try:
            # BuildingNameEnum(value)를 통해 유효한지 확인
            BuildingNameEnum(value)
        except ValueError:
            raise serializers.ValidationError('유효하지 않은 건물명입니다.')
        return value

    def validate_floors(self, value):
        if not value:
            raise serializers.ValidationError('층수를 입력해주세요.')
            
        # 쉼표로 구분된 값을 리스트로 분리
        floor_list = value.split(',')
        validated_floors = []
        
        for floor in floor_list:
            try:
                # 각 값을 정수로 변환
                floor_int = int(floor.strip())
                if floor_int < 1:
                    raise serializers.ValidationError(f'층수는 1 이상이어야 합니다: {floor}')
                validated_floors.append(floor_int)
            except ValueError:
                raise serializers.ValidationError(f'층수는 숫자로 입력해주세요: {floor}')
                
        # 중복 제거하여 정렬된 리스트 반환
        return sorted(set(validated_floors))
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance