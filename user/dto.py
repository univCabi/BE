from rest_framework import serializers
from datetime import datetime
from .models import users
from cabinet.models import cabinets, cabinet_histories
from authn.models import authns

import pytz  # Add this import for timezone handling

class CamelCaseSerializer(serializers.Serializer):
    def to_camel_case(self, snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        return {self.to_camel_case(key): value for key, value in data.items()}

#class RentCabinetInfoDto(serializers.Serializer):
#    building = serializers.CharField(source='building_id.name', help_text='건물')
#    floor = serializers.CharField(source='building_id.floor', help_text='층')
#    cabinetNumber = serializers.IntegerField(source='cabinet_number', help_text='캐비넷 번호')
#    status = serializers.CharField(help_text='상태')
#    startDate = serializers.DateTimeField(source='cabinet_histories.created_at', help_text='사용 시작일')
#    endDate = serializers.DateTimeField(source='cabinet_histories.expired_at', help_text='사용 종료일')
#    leftDate = serializers.SerializerMethodField(help_text='남은 일수')

#    def get_leftDate(self, obj):
#        try:
#            expired_at = obj.cabinet_histories.expired_at
#            current_time = datetime.now()
#            left_date = (expired_at - current_time).days
#            return left_date
#        except Exception:
#            return 0

class GetProfileMeDto(CamelCaseSerializer):
    name = serializers.CharField(help_text='이름')
    affiliation = serializers.CharField(help_text='소속')
    isVisible = serializers.BooleanField(source='is_visible', help_text='이름 공개 여부')
    studentNumber = serializers.SerializerMethodField(help_text='학번')
    phoneNumber = serializers.CharField(source='phone_number', help_text='전화번호')
    rentCabinetInfo = serializers.SerializerMethodField(help_text='캐비넷 정보')

    class Meta:
        model = users
        fields = ['name', 'isVisible', 'affiliation', 'studentNumber', 'phoneNumber', 'rentCabinetInfo']

    def get_studentNumber(self, obj):
        try:
            return obj.authn_info.student_number
        except AttributeError:
            return None
    
    def get_rentCabinetInfo(self, obj):
        cabinet = cabinets.objects.filter(user_id=obj.id).first()
        if not cabinet:
            return None

        try:
            cabinet_history = cabinet_histories.objects.filter(cabinet_id=cabinet.id).latest('expired_at')
        except cabinet_histories.DoesNotExist:
            cabinet_history = None

        # Make `current_time` timezone-aware
        current_time = datetime.now(pytz.UTC)  # Ensure timezone awareness

        # Calculate `leftDate`
        left_date = (
            (cabinet_history.expired_at - current_time).days
            if cabinet_history and cabinet_history.expired_at
            else None
        )

        return {
            'building': cabinet.building_id.name,
            'floor': cabinet.building_id.floor,
            'cabinetNumber': cabinet.cabinet_number,
            'status': cabinet.status,
            'startDate': cabinet_history.created_at if cabinet_history else None,
            'endDate': cabinet_history.expired_at if cabinet_history else None,
            'leftDate': left_date
        }


class UpdateProfileMeDto(serializers.Serializer):
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')