from django.urls import path
from . import views

urlpatterns = [
    path('profile/me', views.ProfileMeView.as_view(), name='profile'),
]
