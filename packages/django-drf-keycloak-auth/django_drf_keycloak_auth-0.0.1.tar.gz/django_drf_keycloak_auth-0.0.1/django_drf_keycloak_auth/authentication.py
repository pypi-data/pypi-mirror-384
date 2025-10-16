from django.contrib.auth.models import User
from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from django_drf_keycloak_auth.keycloak_utils import get_keycloak_openid


class KeycloakAuthentication(BaseAuthentication):
    """Authentication that accepts Keycloak Bearer tokens."""

    def authenticate(self, request: HttpRequest):

        # Get request header of [Authorization: Bearer <token>]
        auth: str = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth or not auth.startswith("Bearer "):
            return None
            # raise AuthenticationFailed("Invalid Authorization header")

        # Get access token from header
        access_token = auth.split(" ", 1)[1].strip()

        keycloak_openid = get_keycloak_openid()

        try:
            # Check whether the token is valid
            result = keycloak_openid.introspect(access_token)
            if not result.get("active"):
                raise AuthenticationFailed("Token is not active")

            # userinfo raises if token invalid
            userinfo = keycloak_openid.userinfo(access_token)
        except Exception as e:
            raise AuthenticationFailed("Invalid access_token")

        username = userinfo.get("preferred_username") or userinfo.get("sub")
        if not username:
            raise AuthenticationFailed("Unable to determine username from access_token")

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"email": userinfo.get("email", "")},
        )
        return (user, None)
