from django.http import HttpResponse
from django.views import View

# Create your views here.

class LoginView(View):
    def get(self, request):
        return HttpResponse('Login')
    
class LogoutView(View):
    def get(self, request):
        return HttpResponse('Logout')