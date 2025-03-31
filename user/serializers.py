from rest_framework import serializers
from datetime import datetime
from .models import users
from cabinet.models import cabinets, cabinet_histories
from authn.models import authns

from univ_cabi.utils import CamelCaseSerializer

import pytz  # Add this import for timezone handling

class GetProfileMeSerializer(CamelCaseSerializer):
    name = serializers.CharField(help_text='이름')
    affiliation = serializers.CharField(help_text='소속')
    isVisible = serializers.BooleanField(source='is_visible', help_text='이름 공개 여부')
    studentNumber = serializers.IntegerField(source='authn_info.student_number', help_text='학번')
    phoneNumber = serializers.CharField(source='phone_number', help_text='전화번호')
    rentCabinetInfo = serializers.SerializerMethodField(help_text='캐비넷 정보')

    class Meta:
        model = users
        fields = ['name', 'isVisible', 'affiliation', 'studentNumber', 'phoneNumber', 'rentCabinetInfo']
    
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


class UserUpdateProfileMeSerializer(serializers.Serializer):
    isVisible = serializers.BooleanField(help_text='이름 공개 여부')

