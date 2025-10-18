from django.http import HttpRequest
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from django_drf_keycloak_auth.keycloak_utils import get_keycloak_openid
from django_drf_keycloak_auth.models.user import User


class KeycloakAuthentication(BaseAuthentication):
    """Authentication that accepts Keycloak Bearer tokens."""

    def authenticate(self, request: HttpRequest):

        # Get request header of [Authorization: Bearer <token>]
        auth: str = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth:
            # If None is returned,
            # it indicates that the authentication class has not authenticated the request.
            # (DRF will continue to try other authentication classes or consider the request anonymous).
            return None
        elif not auth.startswith("Bearer "):
            raise AuthenticationFailed("Invalid token header. No credentials provided.")

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

        user = User(claims=userinfo)
        return (user, access_token)
