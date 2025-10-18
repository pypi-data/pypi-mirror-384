from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):
    """Login: request parameters"""

    redirect_uri = serializers.URLField(help_text="Redirect URI registered in Keycloak")
    nonce = serializers.CharField(help_text="Nonce for OpenID Connect")


class RefreshTokenRequestSerializer(serializers.Serializer):
    """Refresh Token"""

    refresh_token = serializers.CharField(help_text="Refresh token issued by Keycloak")


class RefreshTokenTokenInfoResponseSerializer(serializers.Serializer):
    """Refresh Token: Token Info Response"""

    access_token = serializers.CharField(help_text="Access token issued by Keycloak")
    refresh_token = serializers.CharField(help_text="Refresh token issued by Keycloak")
    id_token = serializers.CharField(help_text="Id token issued by Keycloak")
    scope = serializers.CharField(help_text="Granted scopes")
    token_type = serializers.CharField(help_text="Token type, usually Bearer")
    expires_in = serializers.IntegerField(help_text="Expiration time in seconds")
    refresh_expires_in = serializers.IntegerField(
        help_text="Refresh token expiration time"
    )
    session_state = serializers.CharField(help_text="Session state")


class UserInfoSerializer(serializers.Serializer):
    """User Info"""

    name = serializers.CharField(
        allow_blank=True, required=False, help_text="Full name"
    )
    given_name = serializers.CharField(
        allow_blank=True, required=False, help_text="Given name"
    )
    family_name = serializers.CharField(
        allow_blank=True, required=False, help_text="Family name"
    )
    preferred_username = serializers.CharField(
        allow_blank=True, required=False, help_text="Preferred username"
    )
    email = serializers.EmailField(
        allow_blank=True, required=False, help_text="Email address"
    )
    email_verified = serializers.BooleanField(
        default=False, help_text="Whether the email is verified"
    )
    resource_access = serializers.DictField(
        child=serializers.DictField(),
        default=dict,
        help_text="Access info for resources",
    )
    sub = serializers.CharField(help_text="User ID / subject")


class GenerateTokenRequestSerializer(serializers.Serializer):
    """Generate Token: by Authorization Code"""

    code = serializers.CharField(help_text="Authorization code from Keycloak")
    state = serializers.CharField(help_text="State parameter")
    nonce = serializers.CharField(help_text="Nonce parameter")
    redirect_uri = serializers.URLField(help_text="Redirect URI registered in Keycloak")


class GenerateTokenResponseSerializer(serializers.Serializer):
    """Generate Token: Response"""

    access_token = serializers.CharField(help_text="Access token issued by Keycloak")
    refresh_token = serializers.CharField(help_text="Refresh token issued by Keycloak")
    id_token = serializers.CharField(help_text="Id token issued by Keycloak")
    scope = serializers.CharField(help_text="Granted scopes")
    token_type = serializers.CharField(help_text="Token type, usually Bearer")
    expires_in = serializers.IntegerField(help_text="Expiration time in seconds")
    refresh_expires_in = serializers.IntegerField(
        help_text="Refresh token expiration time"
    )
    userinfo = UserInfoSerializer(required=False, help_text="User info from Keycloak")


class RevokeTokenRequestSerializer(serializers.Serializer):
    """Revoke Token"""

    token = serializers.CharField(help_text="Token issued by Keycloak")
    token_type_hint = serializers.ChoiceField(
        choices=["access_token", "refresh_token"],
        help_text="Type of the token being revoked",
    )


class LogoutRequestSerializer(serializers.Serializer):
    """Logout"""

    refresh_token = serializers.CharField(help_text="Refresh token issued by Keycloak")


class CallbackRequestSerializer(serializers.Serializer):
    """Callback view"""

    code = serializers.CharField(help_text="Authorization code from Keycloak")


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
