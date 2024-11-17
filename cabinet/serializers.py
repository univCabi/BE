from rest_framework import serializers
from .models import cabinets, cabinet_positions, cabinet_histories
from univ_cabi.utils import CamelCaseSerializer



class requestFindAllCabinetInfoByBuildingNameAndFloor(serializers.Serializer):
    buildingName = serializers.CharField(help_text='건물명')
    floor = serializers.CharField(help_text='층수')


class lentCabinetByUserIdAndCabinetId(serializers.Serializer):
    userId = serializers.IntegerField(help_text='유저 ID')
    cabinetId = serializers.IntegerField(help_text='사물함 ID')

class returnCabinetByUserIdAndCabinetId(serializers.Serializer):
    userId = serializers.IntegerField(help_text='유저 ID')
    cabinetId = serializers.IntegerField(help_text='사물함 ID')

class searchCabinetAndBuildingByKeyWord(serializers.Serializer):
    keyword = serializers.CharField(help_text='검색어')

class findAllCabinetHistoryByUserId(serializers.Serializer):
    userId = serializers.IntegerField(help_text='유저 ID')

class cabinetInfoSerializer(serializers.Serializer):
    width = serializers.IntegerField(help_text='사물함 너비')
    height = serializers.IntegerField(help_text='사물함 높이')

# FloorInfo의 각 항목을 정의하는 Serializer
class floorInfoItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text='사물함 ID')
    username = serializers.IntegerField(help_text='유저 ID')
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')
    isMine = serializers.BooleanField(help_text='내 사물함 여부')
    xPos = serializers.IntegerField(help_text='x 좌표')
    yPos = serializers.IntegerField(help_text='y 좌표')
    cabinetNumber = serializers.IntegerField(help_text='사물함 번호')
    status = serializers.CharField(help_text='사물함 상태')
    payable = serializers.CharField(help_text='사물함 요금 상태')

# FloorInfo를 리스트 형태로 정의
class floorInfoSerializer(serializers.ListSerializer):
    child = floorInfoItemSerializer()

class responseFindAllCabinetInfoByBuildingNameAndFloor(serializers.Serializer):
    cabinetInfo = cabinetInfoSerializer(help_text="사물함 정보")
    floorInfo = floorInfoSerializer(many=True, help_text="층별 사물함 리스트")

class CabinetAllInfoSerializer(serializers.ModelSerializer):
    status = serializers.CharField(help_text='상태')  # Ensure this returns a string
    payable = serializers.CharField(help_text='결제 상태')  # Ensure this returns a string

    class Meta:
        model = cabinets
        fields = ['id', 'user_id', 'building_id', 'cabinet_number', 'status', 'payable', 'created_at', 'updated_at', 'deleted_at']

class CabinetHistoryAllInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = cabinet_histories
        fields = '__all__'  # 모든 필드를 직렬화

class CabinetPositionAllInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = cabinet_positions
        fields = '__all__'  # 모든 필드를 직렬화


class CabinetLogDto(CamelCaseSerializer):
    building = serializers.CharField(source='cabinet_id.building_id.name', help_text='건물 이름')
    floor = serializers.IntegerField(source='cabinet_id.building_id.floor', help_text='층')
    section = serializers.CharField(source='cabinet_id.building_id.section', help_text='섹션')
    cabinetNumber = serializers.IntegerField(source='cabinet_id.cabinet_number', help_text='캐비넷 번호')
    startDate = serializers.DateTimeField(source='created_at', help_text='사용 시작일', required=False, allow_null=True)
    endDate = serializers.DateTimeField(source='ended_at', help_text='사용 종료일', required=False, allow_null=True)

    class Meta:
        model = cabinet_histories
        fields = ['building', 'floor', 'section', 'cabinetNumber', 'startDate', 'endDate']

        
class CabinetSearchSerializer(serializers.Serializer):
    keyword = serializers.CharField(required=True, max_length=100)