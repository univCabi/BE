from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.CabinetMainView.as_view() , name='main'),
    #path('search/', views.CabinetSearchView.as_view(), name='search'),
    path('rent/', views.CabinetRentView.as_view(), name='rent'),
    path('return/', views.CabinetReturnView.as_view(), name='return'),
    path('search/', views.CabinetSearchView.as_view(), name='search'),
    path('search/detail/', views.CabinetSearchDetailView.as_view(), name='search_detail'),
    path('test/', views.CabinetTestView.as_view(), name='test'),
]
