from rest_framework import serializers

#TODO: 웅기님 여깁니다 ㅋㅋ ^_^
class RentCabinetInfo(serializers.Serializer):
    building = serializers.CharField(help_text='건물')
    floor = serializers.CharField(help_text='층')
    cabinetNumber = serializers.CharField(help_text='캐비넷 번호')
    status = serializers.CharField(help_text='상태')
    startDate = serializers.DateField(help_text='사용 시작일')
    endDate = serializers.DateField(help_text='사용 종료일')
    leftDate = serializers.IntegerField(help_text='남은 일수')

class GetProfileMe(serializers.Serializer):
    name = serializers.CharField(help_text='이름')
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')
    affiliation = serializers.CharField(help_text='소속')
    studentNumber = serializers.CharField(help_text='학번')
    phoneNumber = serializers.CharField(help_text='전화번호')
    RentCabinetInfo = RentCabinetInfo(help_text='캐비넷 정보')


class UpdateProfileMe(serializers.Serializer):
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')

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