from authn.models import authns
from rest_framework import authentication
from rest_framework import exceptions
from django.contrib.auth.hashers import check_password

class LoginAuthenticate(authentication.BaseAuthentication):
    def authenticate(self, request):
        student_number = request.data.get('student_number')
        password = request.data.get('password')

        if not student_number or not password:
            return None

        try:
            authInfo = authns.objects.get(student_number=student_number)
        except authns.DoesNotExist:
            raise exceptions.AuthenticationFailed('No such user')

        # Verify the password using Django's check_password function
        if not check_password(password, authInfo.password):
            raise exceptions.AuthenticationFailed('Incorrect password')

        return (authInfo, None)