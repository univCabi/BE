from django.urls import path
from . import views

urlpatterns = [
    path('profile/me', views.ProfileMeView.as_view(), name='profile'),
    path('mockup', views.MockupView.as_view(), name='mockup'),
]
