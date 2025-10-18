from functools import partial
from typing import Tuple

from authlib.integrations import requests_client
from termcolor import cprint

from ..config import Settings, settings
from .auth_helpers import _get_session_type, get_credentials_file, update_token
from .exceptions import SSOLoginFailed
from .session import SessionType, build_headers, load_session_info


def login(
    audience: str,
    username: str,
    password: str,
    client_id: str = settings.AUTH0_CLIENT_ID,
    token_url: str = settings.AUTH0_TOKEN_ENDPOINT,
    scope: str = settings.AUTH0_SCOPES,
) -> dict:
    client = requests_client.OAuth2Session(
        client_id=client_id,
    )
    try:
        token = client.fetch_token(
            url=token_url,
            username=username,
            password=password,
            include_client_id=True,
            scope=scope,
            audience=audience,
        )
    except requests_client.OAuthError as exc:
        msg = f"Failed to login with client credentials, details: {exc.error}"
        cprint(msg, "red")
        raise SSOLoginFailed(msg) from exc
    update_token(token, audience)
    return token


def get_session(
    audience: str, input_setting: Settings = settings, session_info: dict = None
) -> Tuple[requests_client.OAuth2Session, SessionType]:
    """
    Return an authorized auth0 session and session type.
    """
    if not session_info:
        credentials_file = get_credentials_file(audience)
        if credentials_file.exists():
            session_info = load_session_info(
                credentials_file=get_credentials_file(audience)
            )

    session = requests_client.OAuth2Session(
        client_id=input_setting.AUTH0_CLIENT_ID,
        token_endpoint=settings.AUTH0_TOKEN_ENDPOINT,
        audience=audience,
        update_token=partial(update_token, audience=audience),
        token=session_info,
    )
    session.headers = build_headers()
    return session, _get_session_type(session_info=session_info)
