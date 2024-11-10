from rest_framework import serializers

#TODO: 웅기님 여깁니다 ㅋㅋ ^_^
class RentCabinetInfoSerializer(serializers.Serializer):
    building = serializers.CharField(help_text='건물')
    floor = serializers.CharField(help_text='층')
    cabinet_number = serializers.CharField(help_text='캐비넷 번호')
    status = serializers.CharField(help_text='상태')
    start_date = serializers.DateField(help_text='사용 시작일')
    end_date = serializers.DateField(help_text='사용 종료일')
    left_date = serializers.IntegerField(help_text='남은 일수')

class GetProfileMeSerializer(serializers.Serializer):
    name = serializers.CharField(help_text='이름')
    is_visible = serializers.BooleanField(help_text='이름 공개 여부')
    affiliation = serializers.CharField(help_text='소속')
    student_number = serializers.CharField(help_text='학번')
    phone_number = serializers.CharField(help_text='전화번호')
    RentCabinetInfoSerializer = RentCabinetInfoSerializer(help_text='캐비넷 정보')


class UpdateProfileMeSerializer(serializers.Serializer):
    is_visible = serializers.BooleanField(help_text='이름 공개 여부')

class UpdateProfileMeDto(serializers.Serializer):
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')

from rest_framework import serializers
from .models import users, buildings

class UserProfileInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = users
        fields = ['id', 'name', 'is_visible', 'affiliation', 'phone_number', 'building_id']


class BuildingAllInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = buildings
        fields = '__all__'  # 모든 필드를 직렬화





#axios.get 요청
#이름

#이름-> 이름 공개할지 안할지 true false

#전공

#학번

#전화번호

#몇관 몇층

#사용 기간

#남은 기간

#종료 일자
#------------------------------------------------
#axios.post 요청
#유저의 위의 데이터 저장