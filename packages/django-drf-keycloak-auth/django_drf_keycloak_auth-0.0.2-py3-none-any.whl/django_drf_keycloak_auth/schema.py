from urllib.parse import urljoin

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object

from django_drf_keycloak_auth.keycloak_utils import KEYCLOAK_REALM, KEYCLOAK_SERVER_URL


class KeycloakBearerScheme(OpenApiAuthenticationExtension):

    target_class = "django_drf_keycloak_auth.authentication.KeycloakAuthentication"
    name = "BearerAuth"

    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name="Authorization",
            token_prefix="Bearer",
        )


# class KeycloakOpenIDScheme(OpenApiAuthenticationExtension):
#     """
#     Register Keycloak authentication as an OpenID Connect security scheme in drf-spectacular.
#     This will add a securityScheme named "OpenID" under components.securitySchemes.
#     Make sure SPECTACULAR_SETTINGS['SECURITY'] references {"OpenID": []} if you want it applied globally.
#     """

#     target_class = "django_drf_keycloak_auth.authentication.KeycloakAuthentication"
#     name = "OpenID"

#     def get_security_definition(self, auto_schema):
#         return {
#             "type": "openIdConnect",
#             "openIdConnectUrl": urljoin(
#                 KEYCLOAK_SERVER_URL.rstrip("/"),
#                 f"/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration",
#             ),
#         }


# class KeycloakOAuth2Scheme(OpenApiAuthenticationExtension):

#     target_class = "django_drf_keycloak_auth.authentication.KeycloakAuthentication"
#     name = "OAuth2"

#     def get_security_definition(self, auto_schema):
#         return {
#             "type": "oauth2",
#             "flows": {
#                 # Use the authorizationCode flow
#                 "authorizationCode": {
#                     "authorizationUrl": urljoin(
#                         KEYCLOAK_SERVER_URL.rstrip("/"),
#                         f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth",
#                     ),
#                     "tokenUrl": urljoin(
#                         KEYCLOAK_SERVER_URL.rstrip("/"),
#                         f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
#                     ),
#                     "scopes": {
#                         "openid": "OpenID connect scope",
#                         "profile": "Access user profile",
#                         "email": "Access user email",
#                     },
#                 }
#             },
#         }
