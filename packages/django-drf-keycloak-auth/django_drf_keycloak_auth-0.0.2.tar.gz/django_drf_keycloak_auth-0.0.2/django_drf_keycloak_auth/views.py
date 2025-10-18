import secrets

from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
)
from keycloak.exceptions import KeycloakPostError
from rest_framework import permissions, status
from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView, Request, Response

from django_drf_keycloak_auth.keycloak_utils import (
    get_keycloak_error_description,
    get_keycloak_openid,
    revoke_token,
)
from django_drf_keycloak_auth.serializers import (
    CallbackRequestSerializer,
    ErrorResponseSerializer,
    GenerateTokenRequestSerializer,
    GenerateTokenResponseSerializer,
    LoginRequestSerializer,
    LogoutRequestSerializer,
    RefreshTokenRequestSerializer,
    RefreshTokenTokenInfoResponseSerializer,
    RevokeTokenRequestSerializer,
)


class LoginView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        auth=[],
        parameters=[
            OpenApiParameter(
                name="redirect_uri",
                type=OpenApiTypes.URI,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Redirect URI registered in Keycloak",
                default="http://localhost:3000/auth/callback",
            ),
            OpenApiParameter(
                name="nonce",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Nonce parameter",
                default="testnonce",
            ),
        ],
        examples=[
            OpenApiExample(
                "Query params example",
                summary="Example query parameters",
                value={
                    "redirect_uri": "https://example.com/callback",
                    "nonce": "noncevalue",
                },
                request_only=True,
            )
        ],
        request=LoginRequestSerializer,
        responses={302: None, 400: [ErrorResponseSerializer]},
        description="Redirect user to Keycloak login page with state and nonce",
    )
    def get(self, request: Request):

        # 1️⃣ Get query parameters
        serializer = LoginRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        redirect_uri = data["redirect_uri"]
        nonce = data["nonce"]

        # 2️⃣ Manually generate random state to prevent CSRF
        state = secrets.token_urlsafe(16)

        # request.session["oauth_state"] = state

        # 3️⃣ Build an authorization URL
        keycloak_openid = get_keycloak_openid()
        auth_url = keycloak_openid.auth_url(
            redirect_uri=redirect_uri,
            nonce=nonce,
            state=state,
            scope="openid profile email",
        )

        # 4️⃣ Redirect to the authorization URL
        return redirect(auth_url)


@method_decorator(csrf_exempt, name="dispatch")
class GenerateTokenView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]
    renderer_classes = [JSONRenderer]

    @extend_schema(
        auth=[],
        parameters=[
            OpenApiParameter(
                name="code",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Authorization code from Keycloak",
            ),
            OpenApiParameter(
                name="state",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="State parameter",
            ),
            OpenApiParameter(
                name="nonce",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Nonce parameter",
                default="testnonce",
            ),
            OpenApiParameter(
                name="redirect_uri",
                type=OpenApiTypes.URI,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Redirect URI registered in Keycloak",
                default="http://localhost:3000/auth/callback",
            ),
        ],
        examples=[
            OpenApiExample(
                "Query params example",
                summary="Example query parameters",
                value={
                    "code": "abc123",
                    "state": "xyz456",
                    "nonce": "noncevalue",
                    "redirect_uri": "https://example.com/callback",
                },
                request_only=True,
            )
        ],
        request=GenerateTokenRequestSerializer,
        responses={
            200: GenerateTokenResponseSerializer,
            400: [GenerateTokenResponseSerializer, ErrorResponseSerializer],
        },
        description="Generate Keycloak access token using authorization code",
    )
    def get(self, request: Request):

        # 1️⃣ Validate request query params
        serializer = GenerateTokenRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 2️⃣ Get Keycloak OpenID client
        keycloak_openid = get_keycloak_openid()

        try:
            # 3️⃣ Get token by code
            token: dict = keycloak_openid.token(
                code=data["code"],
                grant_type="authorization_code",
                redirect_uri=data["redirect_uri"],
            )
        except KeycloakPostError as e:
            return Response(
                {"detail": f"Failed to get token: {get_keycloak_error_description(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 4️⃣ Get user info
            userinfo = keycloak_openid.userinfo(token.get("access_token"))
        except Exception:
            userinfo = {}

        # 5️⃣ Combine the returned data
        response_data = {
            **token,
            "userinfo": userinfo,
        }

        # 6️⃣ Serialize response data
        response_serializer = GenerateTokenResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RefreshTokenView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    @extend_schema(
        auth=[],
        request=RefreshTokenRequestSerializer,
        responses={
            200: RefreshTokenTokenInfoResponseSerializer,
            400: [RefreshTokenTokenInfoResponseSerializer, ErrorResponseSerializer],
        },
        examples=[
            OpenApiExample(
                "Missing refresh_token",
                summary="Refresh token missing",
                value={"refresh_token": ["This field is required."]},
                request_only=False,
                response_only=True,
                status_codes=[status.HTTP_400_BAD_REQUEST],
            ),
            OpenApiExample(
                "Keycloak refresh token failure",
                summary="Failed to refresh token due to Keycloak error",
                value={"detail": "Failed to refresh token: invalid_grant"},
                request_only=False,
                response_only=True,
                status_codes=[status.HTTP_400_BAD_REQUEST],
            ),
        ],
        description="Refresh access token using a refresh token issued by Keycloak",
    )
    def post(self, request: Request):

        # 1️⃣ Validate request body data
        serializer = RefreshTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]

        # 2️⃣ Get Keycloak OpenID client
        keycloak_openid = get_keycloak_openid()

        try:
            # 3️⃣ Get access token by refresh token
            token: dict = keycloak_openid.refresh_token(refresh_token)
        except KeycloakPostError as e:
            return Response(
                {
                    "detail": f"Failed to refresh token: {get_keycloak_error_description(e)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_serializer = RefreshTokenTokenInfoResponseSerializer(data=token)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)


class RevokeTokenView(APIView):
    """
    Stateless endpoint to revoke an access_token or refresh_token in Keycloak.

    Usage examples:
    From body token (e.g. refresh token):
    POST /oauth2/revoke/
    Body: {"token": "<refresh_token>", "token_type_hint": "refresh_token"}

    Behavior:
    - Returns 204 No Content if the revoke call succeeded.
    - Returns 400 if failed
    """

    # No authentication required
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    @extend_schema(
        request=RevokeTokenRequestSerializer,
        responses={
            204: OpenApiTypes.NONE,
            400: [ErrorResponseSerializer],
        },
        examples=[
            OpenApiExample(
                "Missing token",
                summary="Token missing",
                value={"token": ["This field is required."]},
                request_only=False,
                response_only=True,
                status_codes=[status.HTTP_400_BAD_REQUEST],
            ),
            OpenApiExample(
                "Keycloak token invalid",
                summary="Failed to revoke token due to Keycloak error",
                value={"detail": "Failed to revoke token: invalid_token"},
                request_only=False,
                response_only=True,
                status_codes=[status.HTTP_400_BAD_REQUEST],
            ),
        ],
        description="Revoke access or refresh token in Keycloak",
    )
    def post(self, request: Request):

        # Validate request body data
        serializer = RevokeTokenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Get token and token_type_hint from body
        token = serializer.validated_data["token"]
        token_type_hint = serializer.validated_data["token_type_hint"]

        # 5️⃣ Revoke access token
        revoke_token(token, token_type_hint)

        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]
    parser_classes = [JSONParser]
    renderer_classes = [JSONRenderer]

    @extend_schema(
        auth=[],
        request=LogoutRequestSerializer,
        responses={
            204: OpenApiTypes.NONE,
            400: [ErrorResponseSerializer],
        },
        examples=[
            OpenApiExample(
                "Missing refresh_token",
                summary="Refresh token missing",
                value={"refresh_token": ["This field is required."]},
                request_only=False,
                response_only=True,
                status_codes=[status.HTTP_400_BAD_REQUEST],
            ),
            OpenApiExample(
                "Keycloak refresh token failure",
                summary="Failed to refresh token due to Keycloak error",
                value={"detail": "Failed to refresh token: invalid_grant"},
                request_only=False,
                response_only=True,
                status_codes=[status.HTTP_400_BAD_REQUEST],
            ),
        ],
        description="Logout user by invalidating the refresh token in Keycloak",
    )
    def post(self, request: Request):

        # 1️⃣ Validate request body data
        serializer = LogoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh_token"]

        # 2️⃣ Get Keycloak OpenID client
        keycloak_openid = get_keycloak_openid()

        try:
            # 3️⃣ Logout by refresh token
            keycloak_openid.logout(refresh_token)
        except KeycloakPostError as e:
            return Response(
                {"detail": f"Failed to logout: {get_keycloak_error_description(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)


class CallbackView(APIView):

    # No authentication required
    permission_classes = [permissions.AllowAny]

    renderer_classes = [JSONRenderer]

    @extend_schema(
        exclude=True,
        auth=[],
        parameters=[
            OpenApiParameter(
                name="code",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Authorization code from Keycloak",
            ),
        ],
        examples=[
            OpenApiExample(
                "Query params example",
                summary="Example query parameters",
                value={
                    "code": "abc123",
                },
                request_only=True,
            )
        ],
        request=CallbackRequestSerializer,
        responses={
            200: GenerateTokenResponseSerializer,
            400: [GenerateTokenResponseSerializer, ErrorResponseSerializer],
        },
        description="Generate Keycloak access token using authorization code",
    )
    def get(self, request: Request):

        # 1️⃣ Validate request query params
        serializer = CallbackRequestSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 2️⃣ Get Keycloak OpenID client
        keycloak_openid = get_keycloak_openid()

        try:
            # 3️⃣ Get token by code
            token: dict = keycloak_openid.token(
                code=data["code"],
                grant_type="authorization_code",
                redirect_uri="http://localhost:3000/auth/callback",
            )
        except KeycloakPostError as e:
            return Response(
                {"detail": f"Failed to get token: {get_keycloak_error_description(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # 4️⃣ Get user info
            userinfo = keycloak_openid.userinfo(token.get("access_token"))
        except Exception:
            userinfo = {}

        # 5️⃣ Combine the returned data
        response_data = {
            **token,
            "userinfo": userinfo,
        }

        # 6️⃣ Serialize response data
        response_serializer = GenerateTokenResponseSerializer(data=response_data)
        response_serializer.is_valid(raise_exception=True)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
