import os
import time
from pathlib import Path

import jwt

from ..config import settings
from .exceptions import EmptySessionInfo, NotSSOSession, Unauthorized
from .log import logger
from .session import SessionType, load_session_info, save_session_info


def _get_token_claims(token: str) -> dict:
    """
    Get the JWT claims.

    Args:
        token (str): the JWT access token.

    Returns:
        claims (dict): The claims of the token.

    Raises:
        NotSSOSession
    """
    try:
        unverified_headers = jwt.get_unverified_header(token)
        claims = jwt.decode(
            token,
            options={"verify_signature": False},
            algorithms=unverified_headers["alg"],
        )
    except jwt.exceptions.DecodeError as de:
        logger.debug("Can't decode given access token of none JWT type:  %s", de)
        raise NotSSOSession
    return claims


def _get_session_type(
    session_info: dict,
) -> SessionType:
    """
    Get the session info (access token) type.

    Args:
        session_info (dict): an access token payload and fetched from auth0.

    Returns:
        SessionType: the session type

    Raises:
        EmptySessionInfo
    """
    session_type: SessionType = SessionType.APHERIS
    if not session_info:
        raise EmptySessionInfo("Error, can't get session yet, you need to login first!")
    if token := session_info.get("access_token", None):
        claims = _get_token_claims(token)
        if "iss" in claims and claims["iss"] in settings.AUTH0_TOKEN_ENDPOINT:
            session_type: SessionType = SessionType.AUTH0

    return session_type


def _access_token_is_valid(credentials: dict) -> bool:
    """
    Check if the access token is still valid.

    Args:
        credentials (dict): the credentials' dict.

    Returns:
        bool: True if the token is still valid, False otherwise.
    """
    try:
        # TODO (EN-2033): update the access token using refresh token
        #  without user's interaction if possible
        return credentials["expires_at"] > time.time()
    except KeyError:
        return False


def get_login_information() -> dict:
    """
    Get the login information based on the access token of the currently logged-in user.

    Returns:
        claims (dict): contain session information like
            - user email
            - organization
            - environment

    Raises:
        * Unauthorized if the session information cannot be retrieved
    """
    # load the session info
    credentials = load_session_info()

    # get the claims from the access token
    try:
        claims = _get_token_claims(credentials["access_token"])
    except KeyError:
        raise Unauthorized("Invalid token: Missing access token")
    except NotSSOSession:
        raise Unauthorized("Invalid token: Not an SSO session")

    # check if the access token is still valid
    if _access_token_is_valid(credentials):
        return {
            "email": claims.get("https://sso.apheris.com/email", ""),
            "organization": claims.get("https://sso.apheris.com/org_name", ""),
            "env": os.environ.get("APH_ENV", ""),
        }
    else:
        raise Unauthorized("Access token has expired")


def get_credentials_file(audience: str) -> Path:
    """Return the credentials file based on the audience."""
    if audience == settings.AUTH0_AUDIENCE:
        return settings.CREDENTIALS_FILE
    if audience == settings.AUTH0_NODE_AUDIENCE:
        return settings.NODE_CREDENTIALS_FILE

    # TODO: add a better error message
    raise RuntimeError("Unknown audience!")


def update_token(
    token,
    audience: str,
    refresh_token=None,
    access_token=None,
):
    """Save the token after the refresh."""
    save_session_info(token, credentials_file=get_credentials_file(audience))
