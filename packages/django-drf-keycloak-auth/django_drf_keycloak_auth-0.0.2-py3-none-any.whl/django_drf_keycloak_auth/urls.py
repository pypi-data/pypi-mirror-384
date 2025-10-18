"""
URL configuration for django_drf_keycloak_auth project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

# Do not remove this import.
#
# This import ensures that drf-spectacular registers the Keycloak authentication scheme when the module is loaded
import django_drf_keycloak_auth.schema

from . import views

urlpatterns = [
    path("oauth2/login/", views.LoginView.as_view(), name="login"),
    path("oauth2/token/", views.GenerateTokenView.as_view(), name="login"),
    path("oauth2/refresh/", views.RefreshTokenView.as_view(), name="refresh_token"),
    path("oauth2/revoke/", views.RevokeTokenView.as_view(), name="revoke_token"),
    path("oauth2/logout/", views.LogoutView.as_view(), name="logout"),
    path("oauth2/callback/", views.CallbackView.as_view(), name="callback"),
]
