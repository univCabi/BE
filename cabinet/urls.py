from django.urls import path
from . import views

urlpatterns = [
    path('', views.CabinetFloorView.as_view(), name='floor'),
    path('detail', views.CabinetFloorDetailView.as_view(), name='floor_detail'),
    path('rent', views.CabinetRentView.as_view(), name='rent'),
    path('return', views.CabinetReturnView.as_view(), name='return'),

    path('search', views.CabinetSearchView.as_view(), name='search'),
    path('search/detail', views.CabinetSearchDetailView.as_view(), name='search_detail'),
    path('history', views.CabinetHistoryView.as_view(), name='history'),

    path('all', views.CabinetFindAll.as_view(), name='all'),

    path('admin/return', views.CabinetAdminReturnView.as_view(), name='admin_return'),
    path('admin/change/status', views.CabinetAdminChangeStatusView.as_view(), name='admin_change_status'),
]
