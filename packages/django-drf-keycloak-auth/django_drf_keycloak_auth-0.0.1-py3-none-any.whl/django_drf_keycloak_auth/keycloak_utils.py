import os
from functools import cache

from django.conf import settings
from dotenv import load_dotenv
from keycloak import KeycloakOpenID

load_dotenv()

KEYCLOAK_SERVER_URL = os.getenv("KEYCLOAK_SERVER_URL")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET")


@cache
def get_keycloak_settings():
    return {
        "keycloak_server_url": getattr(settings, "KEYCLOAK_SERVER_URL", None),
        "keycloak_realm": getattr(settings, "KEYCLOAK_REALM", None),
        "keycloak_client_id": getattr(settings, "KEYCLOAK_CLIENT_ID", None),
        "keycloak_client_secret": getattr(settings, "KEYCLOAK_CLIENT_SECRET", None),
    }


@cache
def get_keycloak_openid():
    return KeycloakOpenID(
        server_url=KEYCLOAK_SERVER_URL,
        realm_name=KEYCLOAK_REALM,
        client_id=KEYCLOAK_CLIENT_ID,
        client_secret_key=KEYCLOAK_CLIENT_SECRET,
    )
