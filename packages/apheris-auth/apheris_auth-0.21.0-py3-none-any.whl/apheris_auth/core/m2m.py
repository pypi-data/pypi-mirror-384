from functools import partial
from typing import Tuple
from urllib.parse import urlencode

from authlib.integrations import requests_client
from termcolor import cprint

from ..config import settings
from .auth_helpers import get_credentials_file, update_token
from .exceptions import SSOLoginFailed
from .session import load_session_info


def m2m_auth_post(client, method, uri, headers, body, audience) -> Tuple[str, dict, str]:
    """Custom client and secret auth hook."""
    payload = {
        "grant_type": "client_credentials",
        "audience": audience,
        "client_id": client.client_id,
        "client_secret": client.client_secret or "",
    }
    body = urlencode(payload)

    if "Content-Length" in headers:
        headers["Content-Length"] = str(len(body))
    return uri, headers, body


def get_session(
    audience: str,
    token: dict = None,
) -> requests_client.OAuth2Session:
    """Get the existing m2m session."""
    if not token:
        credentials_file = get_credentials_file(audience)
        if credentials_file.exists():
            token = load_session_info(credentials_file=get_credentials_file(audience))

    client = requests_client.OAuth2Session(
        client_id=settings.SERVICE_USER_CLIENT_ID,
        client_secret=settings.SERVICE_USER_CLIENT_SECRET,
        token_endpoint=settings.AUTH0_TOKEN_ENDPOINT,
        grant_type="client_credentials",
        token=token,
        update_token=partial(update_token, audience=audience),
        token_endpoint_auth_method="m2m_auth_post",
    )
    client.register_client_auth_method(
        ("m2m_auth_post", partial(m2m_auth_post, audience=audience))
    )
    return client


def login(audience: str) -> dict:
    """M2M login."""
    client = get_session(audience=audience)
    try:
        token = client.fetch_token(audience=audience)
    except requests_client.OAuthError as exc:
        msg = f"Failed to login with client credentials, details: {exc.error}"
        cprint(msg, "red")
        raise SSOLoginFailed(msg) from exc
    else:
        update_token(token, audience)
        return token
