from rest_framework import serializers

class CabinetSearchSerializer(serializers.Serializer):
    keyword = serializers.CharField(required=True, max_length=100)

