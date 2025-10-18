import os

from termcolor import cprint

from ..config import Settings, settings
from .exceptions import AlreadyLoggedOut, ApherisException, NotSSOSession
from .log import logger
from .session import SessionAudience
from .sso_helper import AuthenticationHelper

authentication_helper = {"apheris": None, "gateway": None}


def sso_login(settings: Settings = settings):
    """Login using the SSO device code flow."""
    try:
        cprint("Logging in to your company account...", "white")
        cprint("Apheris:", "white")
        authentication_helper["apheris"] = AuthenticationHelper(SessionAudience.APHERIS)
        authentication_helper["apheris"].login()
        if not settings.LOGIN_DISABLE_GATEWAY_TOKEN:
            cprint("\n\nGateway:", "white")
            authentication_helper["gateway"] = AuthenticationHelper(
                SessionAudience.COMPUTATION_NODE
            )
            authentication_helper["gateway"].login()
        if os.environ.get("DATABRICKS_RUNTIME_VERSION", None):
            if not settings.LOGIN_DISABLE_GATEWAY_TOKEN:
                print(
                    "To finish the login process call the function below with both "
                    "token urls:\n\n"
                    'apheris_auth.set_login_token(token_url_apheris="http://...", '
                    'token_url_gateway="http://...")'
                )
            else:
                print(
                    "To finish the login process call the function below with the token "
                    "url:\n\n"
                    'apheris_auth.set_login_token("http://...")'
                )
        else:
            cprint("Login was successful", "green")
    except ApherisException as ae:
        logger.debug(f"Login failed {ae}.")
        cprint(f"Login Failed: {ae} ", "red")


def sso_set_login_token(token_url_apheris: str, token_url_gateway: str = "") -> None:
    """
    Since the Databricks notebooks to not support interactive user inputs
    the login process has to be finished manually.

    Args:
            token_url_apheris (ApherisTokenUrl): URL with login tokens for Apheris
            token_url_gateway (GatewayTokenUrl): URL with login tokens for the Gateway
    """
    if not authentication_helper["apheris"]:
        print("Please first call apheris_auth.login()")
        return
    authentication_helper["apheris"].set_login_token(token_url_apheris)
    if token_url_gateway:
        if not authentication_helper["gateway"]:
            print(
                "Please first call apheris_auth.login() with the gateway token enabled."
            )
            return
        authentication_helper["gateway"].set_login_token(token_url_gateway)


def sso_logout(verbose: bool = True):
    """
    Revokes Auth0 refresh token, and deletes the user credential file.

    Args:
        verbose: If True, print information about the logout process.
    Raises:
        AlreadyLoggedOut: when user is already logged out.
    """
    was_logged_in = True
    try:
        AuthenticationHelper(SessionAudience.APHERIS, quiet=not verbose).logout()
    except NotSSOSession:  # otherwise will be hidden by ApherisException below
        raise NotSSOSession
    except ApherisException:
        was_logged_in = False
    try:
        AuthenticationHelper(SessionAudience.COMPUTATION_NODE, quiet=not verbose).logout()
    except ApherisException:
        was_logged_in = was_logged_in or False
    if not was_logged_in:
        raise AlreadyLoggedOut
