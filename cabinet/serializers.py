from rest_framework import serializers



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