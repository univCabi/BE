from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response



# Create your views here.

class CabinetMainView(APIView):
    def get(self, request):
        return HttpResponse('Cabinet Main Page')
    
class CabinetSearchView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({'result': request.GET.get('keyword')})