from django.urls import path
from . import views

urlpatterns = [
    path('login', views.LoginView.as_view() , name='login'),
    path('logout', views.LogoutView.as_view() , name='logout'),

    path('create', views.CreateUserView.as_view() , name='create'),
    path('delete', views.DeleteUserView.as_view() , name='delete'),

    path('token/access', views.ReIssueAccessTokenView.as_view() , name='accessToken'),
    #path('token/refreshToken', views.RefreshTokenView.as_view() , name='refreshToken'),
]
