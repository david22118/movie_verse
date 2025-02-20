from django.urls import path
from .api_views import SignupAPI, LoginAPI, LogoutAPI

urlpatterns = [
    path('signup/', SignupAPI.as_view(), name='signup_api'),
    path('login/', LoginAPI.as_view(), name='login_api'),
    path('logout/', LogoutAPI.as_view(), name='logout_api'),
]
