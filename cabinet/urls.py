from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.CabinetMainView.as_view() , name='main'),

]
