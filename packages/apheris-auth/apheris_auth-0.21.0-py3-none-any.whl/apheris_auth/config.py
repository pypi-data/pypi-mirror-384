import os
import sys
from enum import IntFlag
from operator import xor
from pathlib import Path
from typing import Any, Callable, Iterator, List, Literal, Optional, Union

from pydantic.v1 import AnyHttpUrl, BaseSettings, root_validator


def get_env_file() -> Union[str, os.PathLike]:
    """Supports multiple environment configurations based on the
    APH_ENV environment variable.

    The default environment will be always local.
    """
    # Make sure we don't load a spurious .env file by mistake
    env_name = os.getenv("APH_ENV", "local")
    env_file_prefix = ".env"
    env_file_path = f"{env_file_prefix}-{env_name.lower()}"
    if not os.path.exists(env_file_path):
        return Path(__file__).parent.parent.parent / env_file_path
    return env_file_path


def is_interactive():
    """
    Return whether we are in an interactive environment (e.g. Jupyter notebook) or whether
    we are running a script. The method might not return the correct answer in every case.
    """
    # https://stackoverflow.com/questions/2356399/tell-if-python-is-in-interactive-mode
    return hasattr(sys, "ps1")


class LoginType(IntFlag):
    """
    We support multiple login types and methods, This enum is
    to make some order when each login type is being used.
    """

    LEGACY = 0
    RESOURCE_OWNER = 2 << 1
    CLIENT_CREDENTIALS = 2 << 2
    AUTHORIZATION_CODE_PKCE = 2 << 3

    @classmethod
    def __get_validators__(cls) -> Iterator[Callable[..., Any]]:
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, "LoginType"]) -> "LoginType":
        valid_types = [name for name in dir(LoginType) if not name.startswith("_")]
        value_error = ValueError(
            f"'{v}' Must be an one of `{cls.__name__}` types: " f"{valid_types}"
        )

        if isinstance(v, str):
            try:
                return LoginType[v]
            except KeyError as ke:
                raise value_error from ke
        if not isinstance(v, cls):
            raise value_error
        return v

    @classmethod
    def is_resource_owner_login_type(cls, login_flag: IntFlag) -> bool:
        """
        Checks if the current flag assemble a resource owner login type,
        Resource owner is the username/password login.
        Args:
            login_flag (IntFlag): The current flag to check.

        Returns:
            bool: true if login_flag is resource owner, false otherwise.
        """
        return bool(login_flag & LoginType.RESOURCE_OWNER)


class Settings(BaseSettings):
    LOGIN_TYPE: LoginType = LoginType.AUTHORIZATION_CODE_PKCE
    CLIENT_APP_ID: str = "lFhmB6ru98fH4ivVqeuaV4BKSIpnzm8O3lXJjTP4"
    DEBUG: bool = False
    VERBOSE: bool = is_interactive()
    ENABLE_REFRESH_TOKEN: bool = True
    CLOUD: str = None
    RAISE_PERMISSION_EXCEPTIONS: bool = True
    CREDENTIALS_FILE: Path = Path.home() / ".config/apheris/credentials.json"
    NODE_CREDENTIALS_FILE: Path = Path.home() / ".config/apheris/credentials-node.json"
    # Urls
    API_BASE_URL: AnyHttpUrl = "https://api.app.apheris.net"
    API_SESSION_MAX_RETRIES: int = 8
    CODE_AUDIT_API_BASE_URL: AnyHttpUrl = "https://code-audit.app.apheris.net"
    API_ORCHESTRATOR_BASE_URL: AnyHttpUrl = "https://orchestrator.app.apheris.net"
    API_JOBS_SUBDOMAIN: Optional[str]
    API_AUTHENTICATION_URL: Optional[AnyHttpUrl]
    API_REVOKE_TOKEN_URL: Optional[AnyHttpUrl]
    API_MFA_AUTHENTICATION_URL: Optional[AnyHttpUrl]
    API_DATASETS_URL: Optional[AnyHttpUrl]
    API_ASSET_POLICIES_URL: Optional[AnyHttpUrl]
    API_FLOWS_URL: Optional[AnyHttpUrl]
    API_USER_INFO_URL: Optional[AnyHttpUrl]
    API_DAL_URL: Optional[AnyHttpUrl]

    # SSO
    AUTH0_SSO_ENABLED: bool = False
    AUTH0_BASE_URL: AnyHttpUrl = "https://auth.app.apheris.net"
    AUTH0_AUTHORIZE_ENDPOINT: Optional[AnyHttpUrl]
    AUTH0_TOKEN_ENDPOINT: Optional[AnyHttpUrl]
    AUTH0_REVOKE_REFRESH_TOKEN_ENDPOINT: Optional[AnyHttpUrl]
    AUTH0_AUDIENCE: str = "https://api.app.apheris.net"
    AUTH0_NODE_AUDIENCE: str = "urn:node:apheris:app"
    AUTH0_ALWAYS_REFRESH_NODE_TOKEN: bool = True
    # Auth0 APP specifics
    AUTH0_CLIENT_ID: str = "rcA0bCnWhkzg0SuCDporxRUKUDPBhRt3"
    AUTH0_SCOPES: str = "openid email profile offline_access"
    AUTH0_CALLBACK_URL: str = "https://web.app.apheris.net/authorization-code"
    AUTH0_LOOPBACK_CALLBACK_URL_PATH: str = "authorization-code"
    AUTH0_LOOPBACK_CALLBACK_URL_PORTS: List[int] = [8083, 8085, 8087]

    # Login
    LOGIN_DISABLE_GATEWAY_TOKEN: bool = True
    LOGIN_ORGANIZATION_ID: str = None
    LOGIN_FALLBACK_FLOW: bool = Path(
        "/.dockerenv"
    ).exists()  # TODO: this should be `not path.exists()` but it breaks local flow

    # Serializer, allowed values drived by apheris_statistics.serializers._get_dumpers
    # keys
    DATA_SERIALIZER_NAME: Literal["secure-v1", "pickle-v5"] = "secure-v1"

    # Service user
    SERVICE_USER_CLIENT_ID: Optional[str]
    SERVICE_USER_CLIENT_SECRET: Optional[str]

    STREAMING_CHUNK_SIZE: int = 8 * 1024  # 8K

    # Pre=False is necessary here, with Pre=True the default values are not assigned yet.
    @root_validator(pre=False)
    def set_dependent_variables(cls, values):
        """Set configurations that are dynamic created based on other ones."""
        try:
            api_base_url = values["API_BASE_URL"]
        except KeyError:
            raise RuntimeError(
                f"APH_API_BASE_URL environment variable is not a valid url."
                f"The current value is {os.environ['APH_API_BASE_URL']}, please fix it."
            )

        # Set dependant URL vars
        dependent_envs = (
            ("API_AUTHENTICATION_URL", "/j/token/"),
            ("API_MFA_AUTHENTICATION_URL", "/j/token/code/"),
            ("API_DATASETS_URL", "/datastore/datasets/"),
            ("API_ASSET_POLICIES_URL", "/datastore/asset_policy/"),
            ("API_FLOWS_URL", "/flows/"),
            ("API_USER_INFO_URL", "/accounts/user_info/"),
            ("API_REVOKE_TOKEN_URL", "/j/token/revoke/"),
        )
        for env_name, api_path in dependent_envs:
            values[env_name] = values.get(env_name) or f"{api_base_url}{api_path}"

        try:
            auth0_base_url = values["AUTH0_BASE_URL"]
        except KeyError:
            raise RuntimeError(
                f"AUTH0_BASE_URL environment variable is not a valid url."
                f"The current value is {os.environ['AUTH0_BASE_URL']}, please fix it."
            )

        auth0_dependent_envs = (
            ("AUTH0_AUTHORIZE_ENDPOINT", "/authorize"),
            ("AUTH0_TOKEN_ENDPOINT", "/oauth/token"),
            ("AUTH0_REVOKE_REFRESH_TOKEN_ENDPOINT", "/oauth/revoke"),
        )
        for auth0_env_name, auth0_path in auth0_dependent_envs:
            values[auth0_env_name] = (
                values.get(auth0_env_name) or f"{auth0_base_url}{auth0_path}"
            )

        if xor(
            bool(values["SERVICE_USER_CLIENT_ID"]),
            bool(values["SERVICE_USER_CLIENT_SECRET"]),
        ):
            raise ValueError(
                "Please set both SERVICE_USER_CLIENT_ID and SERVICE_USER_CLIENT_SECRET "
                "to enable login via service account. Or unset both to disable it."
            )

        return values

    def m2m_enabled(self) -> bool:
        """Return the service account configuration status."""
        return bool(self.SERVICE_USER_CLIENT_ID and self.SERVICE_USER_CLIENT_SECRET)

    # TODO: remove this mapping once we
    # change the variable names in the deployed environments.
    class Config:
        env_prefix = "APH_"
        env_file_encoding = "utf-8"


# The .env file is loaded into the environment variables before settings are built
settings = Settings(_env_file=get_env_file())
