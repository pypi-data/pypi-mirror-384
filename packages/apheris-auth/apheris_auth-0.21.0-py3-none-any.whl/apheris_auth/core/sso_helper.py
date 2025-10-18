import os
import time
from pathlib import Path
from typing import Callable, Tuple, Union

import requests
from authlib.integrations import requests_client
from oauthlib import oauth2
from requests_oauthlib import OAuth2Session
from termcolor import cprint

from ..config import LoginType, Settings, settings
from ..external.requests_auth.errors import (
    GrantNotProvided,
    InvalidGrantRequest,
    StateNotProvided,
    TimeoutOccurred,
)
from ..external.requests_auth.oauth2_authentication_responses_server import (
    GrantDetails,
    browser_open_url,
    request_new_grant,
)
from . import m2m, resource_owner_grant
from .auth_helpers import _get_session_type, _get_token_claims
from .exceptions import (
    AllCallbackPortsInUse,
    AlreadyLoggedOut,
    ApherisException,
    EmptySessionInfo,
    FallbackFlow,
    NotSSOSession,
    SSOLoginFailed,
    Unauthorized,
)
from .log import logger
from .session import (
    SessionAudience,
    SessionType,
    build_headers,
    load_session_info,
    save_session_info,
)


class AuthenticationHelper:
    """
    A helper class around SSO and PKCE authorization code flow.
    """

    _CODE_VERIFIER_LENGTH = 43  # The length of the code_verifier, min is 43 bytes

    def __init__(
        self,
        session_audience: SessionAudience = SessionAudience.APHERIS,
        settings: Settings = settings,
        quiet: bool = False,
    ):
        """
        Constructor for the AuthenticationHelper
        Args:
            session_audience (SessionAudience): the target audience for the
                oauth access token.
            settings (Settings): the Settings object to use.
            quiet (bool): If `True`, do not show any prints. This is meant for building
                functionality on top of this class.
        """

        self._fetch_token_request_args: dict = {}
        self._settings: Settings = settings
        self._init_audience_dependent_requirements(session_audience)
        self._init_oauth2_web_app_client()

        self._login_session = OAuth2Session(
            client=self._client, scope=settings.AUTH0_SCOPES
        )
        self._quiet = quiet

    def _cprint_if_not_quiet(self, *args, **kwargs):
        if not self._quiet:
            cprint(*args, **kwargs)

    def _token_updater(self, token: dict):
        """Save the token when it's refreshed."""
        save_session_info(token, credentials_file=self.credentials_file)

    def _init_audience_dependent_requirements(self, session_audience: SessionAudience):
        self._session_audience: SessionAudience = session_audience
        self._credentials_file: Path = self._settings.CREDENTIALS_FILE
        self._audience: str = self._settings.AUTH0_AUDIENCE
        if self._session_audience == SessionAudience.COMPUTATION_NODE:
            self._credentials_file = self._settings.NODE_CREDENTIALS_FILE
            self._audience = self._settings.AUTH0_NODE_AUDIENCE

    def _init_oauth2_web_app_client(self):
        self._code_challenge_method: str = "S256"
        self._code_challenge: Union[str, None] = None
        self._client_id = self._settings.AUTH0_CLIENT_ID
        self._client = oauth2.WebApplicationClient(client_id=self._client_id)

    @property
    def client_id(self) -> str:
        """
        The Client id in use with this instance.
        Returns:
            str
        """
        return self._client_id

    @property
    def credentials_file(self) -> Path:
        """
        The Credentials file in use with this instance.
        Returns:
            Path
        """
        return self._credentials_file

    def login(self):
        """
        Initiates an Authentication and Authorization PKCE authorization code flow.
        It hase several steps:
            * Provide the user with an authorization url.
            * Opens the authorization url in a given browser.
            * Waits and Reads for the user to provide the authorization code callback url.
            * completed the authorization by fetching an access token using
                the authorization code.
        These steps do not work in Databrick notebooks. Therefore only the authorization
        url is displayed and the login has to be completed manually by the user with the
        help of `set_login_token`

        Raises:
            SSOLoginFailed
        """
        if settings.m2m_enabled():
            m2m.login(audience=self._audience)
        elif os.environ.get("DATABRICKS_RUNTIME_VERSION", None):
            self._init_authorization_url(self._settings.AUTH0_CALLBACK_URL)
            self._cprint_if_not_quiet(
                f"Authenticating with {self._session_audience.value}..."
            )
            self._cprint_if_not_quiet(
                'Please open the URL below in a new tab and press the "copy" button.'
            )
            self._cprint_if_not_quiet(self._authorization_url)
        else:
            try:
                if self._settings.LOGIN_FALLBACK_FLOW:
                    # Within a docker environment the localhost
                    # server address is not accessible
                    raise FallbackFlow
                else:
                    self._start_authorization_code_login()
            except (AllCallbackPortsInUse, FallbackFlow):
                self._start_authorization_code_fallback_login()
            self._cprint_if_not_quiet("\n")

            self._finish_login()

    def get_logged_in_session(
        self,
        enforce_refresh: bool = False,
    ) -> Tuple[OAuth2Session, SessionType]:
        """
        Get an already logged-in user session.

        Raises:
            Unauthorized
            NotSSOSession
            EmptySessionInfo

        Returns:
            Tuple[OAuth2Session, SessionType]
        """

        session_info = load_session_info(credentials_file=self.credentials_file)
        if "access_token" not in session_info:
            raise EmptySessionInfo(
                "Error, can't get session yet, you need to login first!"
            )

        if enforce_refresh:
            session_info["expires_in"] = -30  # forces refresh immediately

        session_kw = dict(
            client_id=self.client_id,
            client=self._client,
            scope=self._settings.AUTH0_SCOPES,
            token=session_info,
            token_updater=self._token_updater,
        )

        if (
            self._settings.ENABLE_REFRESH_TOKEN
            or self._session_audience == SessionAudience.COMPUTATION_NODE
        ):
            session_kw.update(
                {
                    "auto_refresh_url": self._settings.AUTH0_TOKEN_ENDPOINT,
                    "auto_refresh_kwargs": {"client_id": self.client_id},
                }
            )

        session = OAuth2Session(**session_kw)
        session.headers = build_headers()
        return session, _get_session_type(session_info=session_info)

    def refresh_token(self):
        """
        Refresh the access token using the refresh token.

        Raises:
            Unauthorized: when the refresh token is invalid.

        """
        if settings.m2m_enabled():
            logger.debug("M2M session does not need to be refreshed.")
            return
        session, session_type = self.get_logged_in_session(enforce_refresh=True)
        if session and "refresh_token" in session.token:
            try:
                logger.debug("Refreshing the access token.")
                new_token = session.refresh_token(
                    token_url=self._settings.AUTH0_TOKEN_ENDPOINT,
                    client_id=self.client_id,
                    refresh_token=session.token["refresh_token"],
                )
                save_session_info(new_token, self.credentials_file)
            except Exception:
                raise Unauthorized("Could not refresh the access token.")

    def logout(self):
        """
        Logs the user out of the SSO session.
        Raises:
            NotSSOSession: when trying to log-out form a non SSO session.
            AlreadyLoggedOut: when user is already logged out.
        """
        try:
            session, session_type = self.get_logged_in_session()
            if session and session_type == SessionType.AUTH0:
                if settings.m2m_enabled():
                    pass
                elif "refresh_token" in session.token:
                    logger.debug("Refresh token will be revoked!")
                    self._revoke_refresh_token(session.token["refresh_token"])
            else:
                logger.debug("Trying to log out from a non SSO session")
                raise NotSSOSession
            self.credentials_file.unlink(missing_ok=True)
        except (Unauthorized, EmptySessionInfo):
            logger.debug("Already logged out")
            raise AlreadyLoggedOut
        self._cprint_if_not_quiet(
            f"Logging out from {self._session_audience.value} session",
            "green",
        )

    def set_login_token(self, token_url: str):
        """
        Set the login token url and finish the login process.
        """
        self._fetch_token_request_args["authorization_response"] = token_url
        self._finish_login()

    def _start_authorization_code_fallback_login(self) -> None:
        self._init_authorization_url(self._settings.AUTH0_CALLBACK_URL)
        self._print_login_instructions_first_step()
        time.sleep(1)
        browser_open_url(self._authorization_url)
        authorization_response = self._get_code_url_callback_from_user()
        self._fetch_token_request_args["authorization_response"] = authorization_response

    def _start_authorization_code_login(self) -> None:
        for port in self._settings.AUTH0_LOOPBACK_CALLBACK_URL_PORTS:
            callback_url = (
                f"http://localhost:{port}/"
                f"{self._settings.AUTH0_LOOPBACK_CALLBACK_URL_PATH}"
            )
            self._init_authorization_url(callback_url)
            logger.debug(
                f"The initialized authorization URL is: {self._authorization_url}"
            )

            timeout = 60 * 2  # 120 sec

            gd = GrantDetails(
                name="code",
                url=self._authorization_url,
                redirect_uri_port=port,
                reception_timeout=timeout,
                session_audience=self._session_audience,
                state=self._state,
            )
            try:
                _, code = request_new_grant(gd)
                self._fetch_token_request_args["code"] = code
                self._print_login_instructions_first_step()
                return
            except OSError:
                continue
            except (
                InvalidGrantRequest,
                TimeoutOccurred,
                GrantNotProvided,
                StateNotProvided,
                oauth2.rfc6749.errors.MismatchingStateError,
            ) as error:
                logger.debug(
                    "Failed to login with authorization code url %s, details %s",
                    self._authorization_url,
                    str(error),
                )
                raise SSOLoginFailed(error)
        raise AllCallbackPortsInUse

    def _finish_login(self) -> None:
        try:
            self._login_session.fetch_token(
                token_url=self._settings.AUTH0_TOKEN_ENDPOINT,
                include_client_id=True,
                **self._fetch_token_request_args,
            )
        except oauth2.rfc6749.errors.OAuth2Error as error:
            authorization_response = self._fetch_token_request_args.get(
                "authorization_response"
            )
            self._cprint_if_not_quiet(
                "Failed to login with authorization code url "
                f"{authorization_response}, details: {error.json}",
                "red",
            )
            if self._settings.LOGIN_FALLBACK_FLOW:
                self._cprint_if_not_quiet(
                    "Please try again and make sure you paste "
                    "the correct information as instructed from the browser.",
                    "yellow",
                )
            raise SSOLoginFailed(f"Failed to login with authorization code {error.json}")
        save_session_info(self._login_session.token, self.credentials_file)

    def _try_get_organization_id(self) -> Union[str, None]:
        """
        Will try to get organization id from an existing session info.
        This will mainly help save a user step entering his organization twice when
        the user authorizes audience for apheris and for computation node.

        Returns:
            org_id or None
        """
        if org_id := self._settings.LOGIN_ORGANIZATION_ID:
            # If an organization id is provided in the settings,
            # it should be the playground
            return org_id

        try:
            session_info = load_session_info(self._settings.CREDENTIALS_FILE)
            if token := session_info.get("access_token", None):
                claims = _get_token_claims(token)
                # TODO: reuse this to m2m and read org id the other claim
                if "org_id" in claims:
                    return claims["org_id"]
        except ApherisException:
            logger.debug("Can't get organization id from token, user is not logged in.")
        return None

    def _init_authorization_url(
        self, callback_url: str = settings.AUTH0_CALLBACK_URL
    ) -> None:
        """
        Initializes and authorization url which the user should open in her/his browser
        and follow onscreen instructions.

        Args:

            callback_url (str): the callback url for the authorization request!
        """
        self._login_session.redirect_uri = callback_url
        code_verifier = self._client.create_code_verifier(self._CODE_VERIFIER_LENGTH)
        self._fetch_token_request_args = {"code_verifier": code_verifier}
        self._code_challenge = self._client.create_code_challenge(
            code_verifier=code_verifier,
            code_challenge_method=self._code_challenge_method,
        )

        self._authorization_url, self._state = self._login_session.authorization_url(
            url=self._settings.AUTH0_AUTHORIZE_ENDPOINT,
            code_challenge=self._code_challenge,
            code_challenge_method=self._code_challenge_method,
            audience=self._audience,
        )
        if organization_id := self._try_get_organization_id():
            self._authorization_url = (
                f"{self._authorization_url}&organization={organization_id}"
            )

        logger.debug(
            f"Authorization url is: {self._authorization_url}, state is: {self._state}"
        )

    def _revoke_refresh_token(self, refresh_token: str = None):
        """
        Revokes Auth0 refresh token, and deletes the user credential file.
        Args:
            refresh_token (str): the refresh_token to be revoked.
        """
        headers = {"content-type": "application/json"}
        payload = {"client_id": self.client_id, "token": refresh_token}
        response = requests.post(
            settings.AUTH0_REVOKE_REFRESH_TOKEN_ENDPOINT,
            json=payload,
            headers=headers,
        )
        response.raise_for_status()

    def _print_login_instructions_first_step(self):
        self._cprint_if_not_quiet(
            f"Authenticating with {self._session_audience.value}...", "yellow"
        )
        self._cprint_if_not_quiet(
            "Please continue the authorization process in your browser.", "yellow"
        )

    def _get_code_url_callback_from_user(self):
        self._cprint_if_not_quiet(
            "Please paste the authorization response "
            "from the browser to continue with the login:",
            "yellow",
        )
        return input()


def get_m2m_session(audience: str) -> Tuple[requests_client.OAuth2Session, SessionType]:
    """Get the m2m session."""
    session = m2m.get_session(audience=audience)
    if not session.token:
        token = m2m.login(audience=audience)
        session.token = token
    return session, _get_session_type(session.token)


def _get_session(
    audience: str, session_audience: SessionAudience
) -> Tuple[OAuth2Session, SessionType]:
    """Internal get session."""
    if settings.m2m_enabled():
        return get_m2m_session(audience=audience)
    elif LoginType.is_resource_owner_login_type(settings.LOGIN_TYPE):
        return resource_owner_grant.get_session(audience=audience)
    else:
        return AuthenticationHelper(session_audience).get_logged_in_session()


def get_session() -> Tuple[OAuth2Session, SessionType]:
    """
    Return an authorized apheris session.
    """
    return _get_session(settings.AUTH0_AUDIENCE, SessionAudience.APHERIS)


def get_node_session() -> Tuple[OAuth2Session, SessionType]:
    """
    Return an authorized node session.
    """
    return _get_session(settings.AUTH0_NODE_AUDIENCE, SessionAudience.COMPUTATION_NODE)


def _login_for_audiences(login: Callable[[str], None]):
    audiences = [settings.AUTH0_AUDIENCE]
    if not settings.LOGIN_DISABLE_GATEWAY_TOKEN:
        audiences = [settings.AUTH0_AUDIENCE, settings.AUTH0_NODE_AUDIENCE]
    for audience in audiences:
        login(audience)


def refresh_token():
    """
    Refresh the access token using the refresh token.

    Raises:
        Unauthorized: when the refresh token is invalid.

    """
    AuthenticationHelper(SessionAudience.APHERIS).refresh_token()
    AuthenticationHelper(SessionAudience.COMPUTATION_NODE).refresh_token()
