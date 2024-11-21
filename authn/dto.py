
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

class LoginSerializer(serializers.Serializer):
    studentNumber = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        studentNumber = data.get('studentNumber')
        password = data.get('password')

        if studentNumber and password:
            user = authenticate(studentNumber=studentNumber, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("User is inactive.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Invalid credentials.")
        else:
            raise serializers.ValidationError("Must include 'studentNumber' and 'password'.")

        return data