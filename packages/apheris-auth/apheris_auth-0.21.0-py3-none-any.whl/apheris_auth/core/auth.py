import logging
from functools import partial
from getpass import getpass
from typing import Literal, Tuple, Union

import requests
from oauthlib import oauth2
from requests.adapters import HTTPAdapter
from requests_oauthlib import OAuth2Session
from termcolor import cprint
from urllib3.util.retry import Retry

from ..config import LoginType, Settings, settings
from . import exceptions, resource_owner_grant
from .api import get_client
from .exceptions import AlreadyLoggedOut, NotSSOSession
from .session import SessionType, build_headers, load_session_info, save_session_info
from .sso_auth import sso_login, sso_logout, sso_set_login_token
from .sso_helper import _login_for_audiences
from .sso_helper import get_session as get_sso_session
from .sso_helper import refresh_token as sso_refresh_token

_client = oauth2.LegacyApplicationClient(client_id=settings.CLIENT_APP_ID)

logger = logging.getLogger("core_auth")
logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)


def get_retry_strategy(max_retries: int = settings.API_SESSION_MAX_RETRIES) -> Retry:
    """Creates a new urlib3 Retry instance.

    The retry strategy will retry on:
        - responses with the status code in the status_forcelist for the allowed_methods
        - all low level errors: connect, read, redirect and others

    For more details please check the documentation here:
    https://urllib3.readthedocs.io/en/stable/reference/urllib3.util.html#urllib3.util.Retry
    """
    return Retry(
        # this includes all types of errors: connect, read, redirect or status errors
        total=max_retries,
        status_forcelist=frozenset({429, 500, 502, 503, 504}),
        backoff_factor=1,
        raise_on_status=True,
        # POST and DELETE are not included since we are not using them
        allowed_methods=frozenset({"GET", "HEAD", "OPTIONS", "PUT"}),
    )


def add_adapters(session: OAuth2Session) -> OAuth2Session:
    """Adds the http and https adapter to the session.

    The adapters are configured with our custom retry strategy.
    """
    adapter = HTTPAdapter(max_retries=get_retry_strategy())
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def get_session() -> Tuple[OAuth2Session, SessionType]:
    """
    Creates a new OAuth2 requests Session.

    The default session_type is apheris if not defined for compatibility.
    SSO sessions should be stored with session_type == "sso".
    """
    try:
        session, session_type = get_sso_session()
    except NotSSOSession:
        logger.debug(
            "Handling a NotSSOSession Exception while getting the logged-in session, "
            "will get it as an Apheris session."
        )
        session = _get_apheris_session()
        session_type = SessionType.APHERIS

    return add_adapters(session), session_type


def token_updater(session_info: dict):
    """Store the new apheris token after refresh."""
    session_info["session_type"] = "apheris"
    save_session_info(session_info)


def _get_apheris_session(
    settings: Settings = settings, session_info: dict = None
) -> OAuth2Session:
    """
    Return an authorized apheris session.
    """
    if not session_info:
        session_info = load_session_info()

    auto_refresh_token_url = None
    auto_refresh_token_kwargs = None

    if settings.ENABLE_REFRESH_TOKEN:
        auto_refresh_token_url = settings.API_AUTHENTICATION_URL
        auto_refresh_token_kwargs = {"client_id": settings.CLIENT_APP_ID}

    session = OAuth2Session(
        client=_client,
        token=session_info,
        auto_refresh_url=auto_refresh_token_url,
        auto_refresh_kwargs=auto_refresh_token_kwargs,
        token_updater=token_updater,
    )
    session.headers = build_headers()
    return session


def __login(username: str, password: str, settings: Settings = settings) -> None:
    """
    Separate function for token fetching with explicit credentials, so it can be used
    by our integration tests. Not to be used by end users.
    """
    try:
        session = OAuth2Session(client=_client)

        def mfa_hook(response):
            """
            This function hooks into the retrieve access token process.
            If the user has enabled MFA, the user gets prompted to provide an MFA code.
            With the provided MFA code a new access token request is sent.

            @param response: the access token response to be checked if MFA login step is
                             required.
            @type response: Response
            @return: response, the final access token response after handling MFA.
            @rtype: Response
            """
            if "ephemeral_token" in response.json():
                data = {}
                data["ephemeral_token"] = response.json()["ephemeral_token"]
                data["client_id"] = settings.CLIENT_APP_ID
                data["code"] = input("MFA code: ")
                response = session.request(
                    method="post", url=settings.API_MFA_AUTHENTICATION_URL, data=data
                )
                if response.status_code != requests.codes.ok:
                    raise exceptions.BadRequest(
                        f"Error loging in: {response.json()['non_field_errors']}"
                    )
            return response

        # Register the MFA hook
        session.register_compliance_hook("access_token_response", mfa_hook)
        credentials = session.fetch_token(
            token_url=settings.API_AUTHENTICATION_URL,
            username=username,
            password=password,
            client_id=settings.CLIENT_APP_ID,
            include_client_id=True,
        )
    except oauth2.InvalidGrantError:
        msg = "Invalid e-mail or password.\nPlease check your credentials."
        raise exceptions.Unauthorized(msg) from None

    token_updater(credentials)


def make_trial_request(refresh_sso_token: bool = False) -> bool:
    """
    Make a trial request to the API to check if the user is logged in.
    In case of failure, try refreshing the SSO token.

    Args:
        refresh_sso_token (bool): If True, refresh the SSO token.

    Returns:
        bool: True if the trial request was successful, False otherwise.
    """
    try:
        if refresh_sso_token:
            # Refresh the SSO token
            sso_refresh_token()
        # Attempt to get user info
        get_client().get_user_info()
        return True
    except Exception as exc:
        logger.debug(f"Trial request failed: {exc}")
        if refresh_sso_token:
            # If after the token refresh unauthorized, perform a recovery process
            try:
                # Recover from wrong state by performing a logout
                logout(verbose=False)
            except NotSSOSession:
                # Revoke access token
                _logout()
            except AlreadyLoggedOut:
                pass
        else:
            # Reattempt to make the trial request after refreshing the token
            return make_trial_request(refresh_sso_token=True)
    return False


def is_logged_in() -> bool:
    """
    Check if the user is logged in.
    Make a trial request to the API to check if the user is logged in.

    Returns:
        bool: True if the request has been successful, False otherwise.
    """
    return make_trial_request()


def login(
    username: str = None,
    password: str = None,
    login_mode: Union[None, Literal["sso"]] = "sso",
) -> None:
    """
    Authenticate a user, either through their Apheris account
    or using their company account. Programmatic login can be achieved
    by supplying the apheris username/passwords directly.
    Alternatively the user can jump right through to using their company login
    by setting the login mode to "sso"
    """
    try:
        if username and password:
            if settings.LOGIN_TYPE == LoginType.LEGACY:
                __login(username, password)
                return
            else:
                _login_for_audiences(
                    partial(
                        resource_owner_grant.login, username=username, password=password
                    )
                )
                return

        if login_mode == "sso":
            if not is_logged_in():
                sso_login()
            else:
                cprint("You are already logged in", "green")
            return

        answer = input(
            """Please type 1 or 2 to specify how you would like to login:
      1. With your Apheris account
      2. With your company account
      (1|2): """
        )

        if answer == "2":
            if not is_logged_in():
                cprint(
                    "Please note this is a two step process and you "
                    "will be asked to interact with this application "
                    "during each of the steps",
                    color="grey",
                    on_color="on_white",
                    attrs=["bold"],
                )
                sso_login()
            else:
                cprint("You are already logged in", "green")
        elif answer == "1":
            if not username:
                username = input("E-mail: ")
            if not password:
                password = getpass()
            if settings.LOGIN_TYPE == LoginType.LEGACY:
                __login(username, password)
            else:
                _login_for_audiences(
                    partial(
                        resource_owner_grant.login, username=username, password=password
                    )
                )
        else:
            cprint("Invalid answer, please provide either 1 or 2", "red")
    except KeyboardInterrupt:
        cprint("\nLogin aborted by user...", "red")


# ToDo: remove deprecated argument (DSE-1524)
def set_login_token(token_url_apheris: str, token_url_gateway: str = "") -> None:
    """
    Since the Databricks notebooks to not support interactive user inputs
    the login process has to be finished manually.

    Args:
            token_url_apheris (ApherisTokenUrl): URL with login tokens for Apheris
            token_url_gateway (GatewayTokenUrl): This setting is deprecated and will be
                removed in future releases
    """
    if token_url_gateway:
        cprint(
            "The gateway token URL is deprecated and will be removed in future releases",
            "yellow",
        )
    sso_set_login_token(token_url_apheris, "")


def logout(verbose: bool = True) -> None:
    """
    Logs the user out.

    Args:
        verbose: If True, print information on logout process.
    """
    try:
        sso_logout(verbose=verbose)
    except exceptions.NotSSOSession:
        logger.debug("Will logout form an Apheris session.")
        # revoke apheris access token
        _logout()
    except exceptions.AlreadyLoggedOut:
        logger.debug("It appears that you are already logged out!")
        if verbose:
            cprint("Already logged out", "green")
        return
    if verbose:
        cprint("Successfully logged out", "green")


def _logout():
    """
    Revokes the Apheris access token and deleted the credentials file.
    """
    try:
        session_info = load_session_info()
    except exceptions.Unauthorized:
        raise exceptions.AlreadyLoggedOut

    access_token = session_info["access_token"]
    refresh_token = session_info["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {"refresh_token": refresh_token}
    response = requests.post(
        settings.API_REVOKE_TOKEN_URL,
        data=data,
        headers=headers,
    )

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        result = exc.response.json()
        status_code = exc.response.status_code
        if status_code == 401 and result["code"] == "token_not_valid":
            # if the token was already blacklisted just remove the file
            pass
        else:
            raise
    finally:
        settings.CREDENTIALS_FILE.unlink(missing_ok=True)
