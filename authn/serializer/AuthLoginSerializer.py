from rest_framework import serializers

class AuthLoginSerializer(serializers.Serializer):
    studentNumber   = serializers.CharField(help_text='학번')
    password         = serializers.CharField(help_text='비밀번호')