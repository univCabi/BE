from rest_framework import serializers

from cabinet.models import cabinet_histories
from univ_cabi.utils import CamelCaseSerializer

class CabinetHistorySerializer(CamelCaseSerializer):
    building = serializers.CharField(source='cabinet_id.building_id.name', help_text='건물 이름')
    floor = serializers.IntegerField(source='cabinet_id.building_id.floor', help_text='층')
    section = serializers.CharField(source='cabinet_id.building_id.section', help_text='섹션')
    cabinetNumber = serializers.IntegerField(source='cabinet_id.cabinet_number', help_text='캐비넷 번호')
    startDate = serializers.DateTimeField(source='created_at', help_text='사용 시작일', required=False, allow_null=True)
    endDate = serializers.DateTimeField(source='ended_at', help_text='사용 종료일', required=False, allow_null=True)

    class Meta:
        model = cabinet_histories
        fields = ['building', 'floor', 'section', 'cabinetNumber', 'startDate', 'endDate']

        
