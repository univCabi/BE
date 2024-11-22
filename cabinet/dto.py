from rest_framework import serializers
from user.models import BuildingNameEnum

class CabinetFloorQueryParamDto(serializers.Serializer):
    building = serializers.CharField(help_text='건물명')
    #section = serializers.CharField(help_text='구역')
    floor = serializers.IntegerField(help_text='층수', min_value=1)

    def validate_building(self, value):
        try:
            # BuildingNameEnum(value)를 통해 유효한지 확인
            BuildingNameEnum(value)
        except ValueError:
            raise serializers.ValidationError('유효하지 않은 건물명입니다.')
        return value
    
    #def validate_section(self, value):
    #    if not isinstance(value, str):
    #        raise serializers.ValidationError('구역은 문자열로 입력해주세요.')
    #    return value

    def validate_floor(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('층수는 숫자로 입력해주세요.')
        return value
    
class CabinetRentDto(serializers.Serializer):
    cabinetId = serializers.IntegerField(help_text='사물함 ID', min_value=1)

    def validate_cabinetId(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('사물함 ID는 숫자로 입력해주세요.')
        return value
    
class CabinetReturnDto(serializers.Serializer):
    cabinetId = serializers.IntegerField(help_text='사물함 ID', min_value=1)

    def validate_cabinetId(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('사물함 ID는 숫자로 입력해주세요.')
        return value
    
#TODO: escape 처리
class CabinetFloorDetailDto(serializers.Serializer):
    cabinetId = serializers.IntegerField(help_text='사물함 ID', min_value=1)

    def validate_cabinetId(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('사물함 ID는 숫자로 입력해주세요.')
        return value


class SearchDto(serializers.Serializer):
    keyword = serializers.CharField(help_text='검색어')

    def validate_keyword(self, value):
        if value is None:
            raise serializers.ValidationError('검색어를 입력해주세요.')
        elif not isinstance(value, int) and len(value) < 2  :
            raise serializers.ValidationError('검색어는 2글자 이상 입력해주세요.')
        return value

class SearchDetailDto(serializers.Serializer):
    keyword = serializers.CharField(help_text='검색어')

    def validate_keyword(self, value):
        if value is None:
            raise serializers.ValidationError('검색어를 입력해주세요.')
        elif not isinstance(value, int) and len(value) < 2  :
            raise serializers.ValidationError('검색어는 2글자 이상 입력해주세요.')
        return value