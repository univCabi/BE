from rest_framework import serializers

from core.validate.base import BaseValidatedSerializer

from core.exception.exceptions import GlobalDtoValidationException

class CabinetPaginatedDto(BaseValidatedSerializer):
    page = serializers.IntegerField(help_text='페이지 번호', default=1)
    pageSize = serializers.IntegerField(help_text='페이지 크기', default=10)
    
    @classmethod
    def create_validated(cls, data):
        """DTO를 생성하고 검증, 실패 시 예외 발생"""
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance