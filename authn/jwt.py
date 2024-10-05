from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.hashers import make_password

# student_number를 hash 시켜서 담습니다
class CustomLoginJwtToken(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # Generate the token using the superclass method
        token = super().get_token(user)

        # Customize the token payload to include student_number instead of user_id
        token['student_number'] = make_password(user.student_number)

        # Optionally, remove user_id if you don't want it
        if 'user_id' in token:
            del token['user_id']

        return token