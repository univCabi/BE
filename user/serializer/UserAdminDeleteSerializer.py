from rest_framework import serializers

class UserAdminDeleteSerializer(serializers.Serializer):
    id = serializers.IntegerField()