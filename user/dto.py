from rest_framework import serializers


class RentCabinetInfoDto(serializers.Serializer):
    building = serializers.CharField(help_text='건물')
    floor = serializers.CharField(help_text='층')
    cabinetNumber = serializers.CharField(help_text='캐비넷 번호')
    status = serializers.CharField(help_text='상태')
    startDate = serializers.DateField(help_text='사용 시작일')
    endDate = serializers.DateField(help_text='사용 종료일')
    leftDate = serializers.IntegerField(help_text='남은 일수')

class GetProfileMeDto(serializers.Serializer):
    name = serializers.CharField(help_text='이름')
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')
    affiliation = serializers.CharField(help_text='소속')
    studentNumber = serializers.CharField(help_text='학번')
    phoneNumber = serializers.CharField(help_text='전화번호')
    RentCabinetInfoDto = RentCabinetInfoDto(help_text='캐비넷 정보')

class UpdateProfileMeDto(serializers.Serializer):
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')

