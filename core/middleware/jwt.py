from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
import os

from cryptography.fernet import Fernet

key = os.environ.get('SECRET_ENCRYPTION_KEY')
cipher_suite = Fernet(key)

# student_number를 hash 시켜서 담습니다
class CustomLoginJwtToken(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        # Generate the token using the superclass method
        token = super().get_token(user)

        # Customize the token payload to include student_number instead of user_id

        print('token:', token)
        # Optionally, remove user_id if you don't want it
        if 'student_number' in token:
            token['student_number'] = encrypt_student_number(user.student_number)
            
        return token
    


def encrypt_student_number(plain_text):
    """주어진 평문을 암호화하여 반환"""
    return cipher_suite.encrypt(plain_text.encode()).decode()

def decrypt_student_number(encrypted_text):
    """암호화된 텍스트를 복호화하여 반환"""
    return cipher_suite.decrypt(encrypted_text.encode()).decode()
