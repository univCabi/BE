from rest_framework import serializers

#TODO: 웅기님 여깁니다 ㅋㅋ ^_^

class RentCabinetInfoDto(serializers.Serializer):
    building = serializers.CharField(source='building_id.name', help_text='건물')  # snake_case -> camelCase
    floor = serializers.CharField(source='building_id.floor', help_text='층')
    cabinetNumber = serializers.CharField(source='cabinet_number', help_text='캐비넷 번호')
    status = serializers.CharField(help_text='상태')
    startDate = serializers.DateField(source='created_at', help_text='사용 시작일')
    endDate = serializers.DateField(source='deleted_at', help_text='사용 종료일')
    leftDate = serializers.IntegerField(help_text='남은 일수')  # 수동 계산이 필요할 경우 SerializerMethodField 사용

    class Meta:
        fields = ['building', 'floor', 'cabinetNumber', 'status', 'startDate', 'endDate', 'leftDate']

class GetProfileMeDto(serializers.Serializer):
    name = serializers.CharField(help_text='이름')
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')
    affiliation = serializers.CharField(help_text='소속')
    studentNumber = serializers.CharField(help_text='학번')
    phoneNumber = serializers.CharField(help_text='전화번호')
    RentCabinetInfo = RentCabinetInfoDto(help_text='캐비넷 정보')

    class Meta:
        fields = ['name', 'isVisible', 'affiliation', 'studentNumber', 'phoneNumber', 'RentCabinetInfo']
    

class UpdateProfileMeDto(serializers.Serializer):
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