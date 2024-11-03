from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.CabinetMainView.as_view() , name='main'),
    path('search/', views.CabinetSearchView.as_view(), name='search'),

]
