from django.http import HttpResponse
from django.views import View

# Create your views here.

class CabinetMainView(View):
    def get(self, request):
        return HttpResponse('Cabinet Main Page')