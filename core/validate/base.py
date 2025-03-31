from rest_framework import serializers

from core.exception.exceptions import GlobalDtoValidationException

class BaseValidatedSerializer(serializers.Serializer):
    @classmethod
    def create_validated(cls, data):
        instance = cls(data=data)
        if not instance.is_valid():
            raise GlobalDtoValidationException(instance.errors)
        return instance