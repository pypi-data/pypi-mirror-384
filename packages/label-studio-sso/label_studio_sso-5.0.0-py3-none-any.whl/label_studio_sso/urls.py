"""
URL configuration for Label Studio SSO.
"""

from django.urls import path

from .views import issue_sso_token

urlpatterns = [
    path("api/sso/token", issue_sso_token, name="sso_token"),
]
