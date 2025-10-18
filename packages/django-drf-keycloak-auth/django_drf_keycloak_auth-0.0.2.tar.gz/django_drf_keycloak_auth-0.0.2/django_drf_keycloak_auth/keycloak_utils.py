import os
from functools import cache
from typing import Optional
from urllib.parse import urljoin

import httpx
from django.conf import settings
from django.http import HttpRequest
from dotenv import load_dotenv
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakOperationError
from rest_framework import status
from rest_framework.exceptions import ValidationError

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


def get_access_token_from_header(request: HttpRequest) -> Optional[str]:

    # Get request header of [Authorization: Bearer <token>]
    auth: str = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth or not auth.startswith("Bearer "):
        return None

    return auth.split(" ", 1)[1].strip()


def get_keycloak_error_description(error: KeycloakOperationError) -> str:

    error_message = error.error_message

    try:
        error_dict = error_message if isinstance(error_message, dict) else {}
        if "error_description" in error_dict:
            return error_dict["error_description"]
        elif "error" in error_dict:
            return error_dict["error"]
    except Exception:
        return error_message


def revoke_token(
    token: str,
    token_type_hint: str,
):
    """
    Revoke an access token or a refresh token.

    return:
    - None if success
    - raise ValidationError if failed
    """

    revoke_url = urljoin(
        KEYCLOAK_SERVER_URL.rstrip("/"),
        f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/revoke",
    )

    data = {
        "token": token,
        "token_type_hint": token_type_hint,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
    }

    with httpx.Client() as client:
        response = client.post(revoke_url, data=data)

    response.raise_for_status()

    if response.text:
        error: dict = response.json()
        raise ValidationError(
            detail=error.get("error_description"), code=status.HTTP_400_BAD_REQUEST
        )


async def a_revoke_token(
    token: str,
    token_type_hint: str,
):
    """
    Revoke an access token or a refresh token.

    return:
    - None if success
    - raise ValidationError if failed
    """

    revoke_url = urljoin(
        KEYCLOAK_SERVER_URL.rstrip("/"),
        f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/revoke",
    )

    data = {
        "token": token,
        "token_type_hint": token_type_hint.value,
        "client_id": KEYCLOAK_CLIENT_ID,
        "client_secret": KEYCLOAK_CLIENT_SECRET,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(revoke_url, data=data)

    response.raise_for_status()

    if response.text:
        error: dict = response.json()
        raise ValidationError(
            detail=error.get("error_description"), code=status.HTTP_400_BAD_REQUEST
        )
