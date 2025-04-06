from django.urls import path
from .presentation import views

urlpatterns = [
    path('profile/me', views.UserProfileMeView.as_view(), name='profile'),

    path('admin/user/create', views.AdminUserCreateView.as_view(), name='user_create'),
    path('admin/user/delete', views.AdminUserDeleteView.as_view(), name='user_delete'),


    path('mockup', views.MockupView.as_view(), name='mockup'),
]
