import secrets

from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from keycloak.exceptions import KeycloakPostError
from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from django_drf_keycloak_auth.keycloak_utils import get_keycloak_openid
from django_drf_keycloak_auth.vo.UserInfoVO import AuthorizeInfoVO, TokenInfoVO

# from .permissions import HasAnyRole, IsEmployeeRole


class LoginView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]

    def get(self, request: Request):

        # Get query parameters
        redirect_uri = request.query_params.get("redirect_uri")
        nonce = request.query_params.get("nonce")

        # Manually generate random state to prevent CSRF
        state = secrets.token_urlsafe(16)

        # request.session["oauth_state"] = state

        # Build an authorization URL
        keycloak_openid = get_keycloak_openid()
        auth_url = keycloak_openid.auth_url(
            redirect_uri=redirect_uri,
            nonce=nonce,
            state=state,
            scope="openid profile email",
        )

        return redirect(auth_url)


@method_decorator(csrf_exempt, name="dispatch")
class GenerateTokenView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]

    renderer_classes = [JSONRenderer]

    def get(self, request: Request):

        code = request.query_params.get("code")
        state = request.query_params.get("state")
        nonce = request.query_params.get("nonce")
        redirect_uri = request.query_params.get("redirect_uri")
        if not code or not state or not nonce or not redirect_uri:
            return Response(
                {"detail": "missing code, state, nonce or redirect_uri"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        keycloak_openid = get_keycloak_openid()

        try:
            # Get token by code
            token: dict = keycloak_openid.token(
                code=code,
                grant_type="authorization_code",
                redirect_uri=redirect_uri,
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to get token: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = token.get("access_token")
            userinfo = keycloak_openid.userinfo(access_token)
        except Exception:
            userinfo = {}

        authorizeInfoVO = AuthorizeInfoVO.model_validate(
            {
                **token,
                "userinfo": userinfo,
            }
        )

        return Response(authorizeInfoVO.model_dump(), status=status.HTTP_200_OK)


class CallbackView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]

    renderer_classes = [JSONRenderer]

    def get(self, request: Request):

        code = request.query_params.get("code")
        state = request.query_params.get("state")
        if not code:
            return Response(
                {"detail": "missing code"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not state or state != request.session.get("oauth_state"):
            return Response(
                {"detail": "Invalid state"}, status=status.HTTP_400_BAD_REQUEST
            )

        keycloak_openid = get_keycloak_openid()

        try:
            # 使用 code 获取 token
            token: dict = keycloak_openid.token(
                code=code,
                grant_type="authorization_code",
                redirect_uri="redirect_uri",
            )
        except Exception as e:
            return Response(
                {"detail": f"Failed to get token: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            access_token = token.get("access_token")
            userinfo = keycloak_openid.userinfo(access_token)
        except Exception:
            userinfo = {}

        authorizeInfoVO = AuthorizeInfoVO.model_validate(
            {
                **token,
                "userinfo": userinfo,
            }
        )

        return Response(authorizeInfoVO.model_dump(), status=status.HTTP_200_OK)


class RefreshTokenView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]

    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    def post(self, request: Request):

        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "missing refresh_token"}, status=status.HTTP_400_BAD_REQUEST
            )

        keycloak_openid = get_keycloak_openid()

        try:
            # Get access token by refresh token
            token: dict = keycloak_openid.refresh_token(refresh_token)
        except KeycloakPostError as e:
            return Response(
                {"detail": f"Failed to refresh token: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        tokenInfoVO = TokenInfoVO.model_validate(token)

        return Response(tokenInfoVO.model_dump(), status=status.HTTP_200_OK)


class LogoutView(APIView):

    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    def post(self, request: Request):

        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"detail": "missing refresh_token"}, status=status.HTTP_400_BAD_REQUEST
            )

        keycloak_openid = get_keycloak_openid()

        try:
            logout_url = keycloak_openid.logout(refresh_token)
            print(logout_url)
            return Response({"detail": "Logged out"}, status=status.HTTP_200_OK)
        except KeycloakPostError as e:
            return Response(
                {"detail": f"Failed to logout: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


# #################################


# class PublicView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def get(self, request):
#         return Response({"message": "this is public"})


# class ProtectedView(APIView):
#     def get(self, request):
#         user = getattr(request, "user", None)
#         return Response(
#             {
#                 "message": "protected",
#                 "user": getattr(user, "username", None),
#                 "claims": getattr(user, "claims", None),
#             }
#         )


# class EmployeeOnlyView(APIView):
#     permission_classes = [IsEmployeeRole]

#     def get(self, request):
#         return Response({"message": "employee only access"})


# class AnyRoleView(APIView):
#     permission_classes = [HasAnyRole]

#     def get(self, request):
#         return Response({"message": "authenticated + any role present"})
