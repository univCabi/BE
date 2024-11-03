from cryptography.fernet import Fernet
from univ_cabi.settings import env

# 암호화 객체 생성

key = env('SECRET_ENCRYPTION_KEY')
cipher_suite = Fernet(key)

def encrypt_student_number(plain_text):
    """주어진 평문을 암호화하여 반환"""
    return cipher_suite.encrypt(plain_text.encode()).decode()

def decrypt_student_number(encrypted_text):
    """암호화된 텍스트를 복호화하여 반환"""
    return cipher_suite.decrypt(encrypted_text.encode()).decode()
