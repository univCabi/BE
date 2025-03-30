from rest_framework import serializers
from building.models import BuildingNameEnum
from authn.models import RoleEnum

#TODO: 비밀번호 정책
class AdminUserCreateSerializer(serializers.Serializer):
    name = serializers.CharField(help_text='이름')
    affiliation = serializers.CharField(help_text='소속')
    phoneNumber = serializers.CharField(help_text='전화번호')
    studentNumber = serializers.CharField(help_text='학번')
    password = serializers.CharField(help_text='비밀번호')
    role = serializers.CharField(help_text='역할')
    buildingName = serializers.CharField(help_text='건물명')
    floor = serializers.IntegerField(help_text='층수')
    section = serializers.CharField(help_text='구역')

    def validate_name(self, value) :
        if value is None:
            raise serializers.ValidationError('이름을 입력해주세요.')
        return value
    
    def validate_affiliation(self, value) :
        if value is None:
            raise serializers.ValidationError('소속을 입력해주세요.')
        return value
    
    def validate_phoneNumber(self, value) :
        if value is None:
            raise serializers.ValidationError('전화번호를 입력해주세요.')
        return value
    
    def validate_studentNumber(self, value) :
        if value is None:
            raise serializers.ValidationError('학번을 입력해주세요.')
        return value
    
    def validate_password(self, value) :
        if value is None:
            raise serializers.ValidationError('비밀번호를 입력해주세요.')
        return value
    
    def validate_role(self, value):
        try:
            RoleEnum(value)
        except ValueError:
            raise serializers.ValidationError('유효하지 않은 역할입니다.')
        return value

    def validate_buildingName(self, value):
        try:
            BuildingNameEnum(value)
        except ValueError:
            raise serializers.ValidationError('유효하지 않은 건물명입니다.')
        return value
    
    def validate_floor(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError('층수는 숫자로 입력해주세요.')
        return value
    
    def validate_section(self, value):
        if value is None:
            raise serializers.ValidationError('구역을 입력해주세요.')
        return value



class AdminUserDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()