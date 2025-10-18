from importlib.metadata import PackageNotFoundError, version

from .core.auth import login, logout, set_login_token

try:
    __version__ = version("apheris-auth")
except PackageNotFoundError:
    __version__ = "UNDEFINED"


def version():
    """
    Current version of Apheris Auth.
    """
    return __version__


__all__ = ["login", "set_login_token", "logout", "version"]
