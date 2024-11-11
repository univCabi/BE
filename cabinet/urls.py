from django.urls import path
from . import views

urlpatterns = [
    path('rent/', views.CabinetRentView.as_view(), name='rent'),
    path('return/', views.CabinetReturnView.as_view(), name='return'),
    path('search/', views.CabinetSearchView.as_view(), name='search'),
    path('search/detail/', views.CabinetSearchDetailView.as_view(), name='search_detail'),
    path('test/', views.CabinetTestView.as_view(), name='test'),
    path('log/', views.CabinetLogView.as_view(), name='log'),
    #path('/', views.CabinetMainView.as_view(), name='main'),
    path('', views.CabinetFloorView.as_view(), name='floor'),
]
