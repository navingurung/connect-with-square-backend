import secrets
from typing import Any
from urllib.parse import urlencode

import requests

from app.config import settings
from app.services.square_client import SquareAPIError


def build_square_oauth_url() -> tuple[str, str]:
    state = secrets.token_urlsafe(32)

    params = {
        "client_id": settings.SQUARE_APPLICATION_ID,
        "scope": settings.SQUARE_SCOPES,
        "session": "false",
        "state": state,
    }

    auth_url = f"{settings.SQUARE_BASE_URL}/oauth2/authorize?{urlencode(params)}"

    return auth_url, state


def exchange_code_for_token(code: str) -> dict[str, Any]:
    url = f"{settings.SQUARE_BASE_URL}/oauth2/token"

    payload = {
        "client_id": settings.SQUARE_APPLICATION_ID,
        "client_secret": settings.SQUARE_APPLICATION_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.SQUARE_REDIRECT_URI,
    }

    headers = {
        "Square-Version": settings.SQUARE_VERSION,
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise SquareAPIError(
            status_code=500,
            detail={"message": "Square OAuth token request failed", "error": str(exc)},
        ) from exc

    try:
        data = response.json()
    except ValueError:
        data = {"message": response.text}

    if response.status_code >= 400:
        raise SquareAPIError(status_code=response.status_code, detail=data)

    return data


def revoke_square_token(access_token: str) -> None:
    """
    Revoke Square access token via Square's OAuth revoke API.
    This forces Square to show the authorization page again on next OAuth.
    """
    url = f"{settings.SQUARE_BASE_URL}/oauth2/revoke"

    payload = {
        "client_id": settings.SQUARE_APPLICATION_ID,
        "access_token": access_token,
    }

    headers = {
        "Square-Version": settings.SQUARE_VERSION,
        "Authorization": f"Client {settings.SQUARE_APPLICATION_SECRET}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise SquareAPIError(
            status_code=500,
            detail={"message": "Square token revocation failed", "error": str(exc)},
        ) from exc

    if response.status_code >= 400:
        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}
        raise SquareAPIError(status_code=response.status_code, detail=data)