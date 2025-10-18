import json
from enum import Enum, IntEnum
from pathlib import Path

from ..config import settings
from . import exceptions
from .log import logger


class SessionType(IntEnum):
    APHERIS = 0
    AUTH0 = 1


class SessionAudience(Enum):
    APHERIS = "Apheris Cloud Platform"
    COMPUTATION_NODE = "Apheris Compute environments"


def load_session_info(credentials_file: Path = settings.CREDENTIALS_FILE) -> dict:
    """
    Return the session info saved on the user's machine.
    Raise Unauthorized if the session can't be loaded.
    """
    logger.debug("loading from file: %s", credentials_file)
    if not credentials_file.exists():
        raise exceptions.Unauthorized(
            "You are not logged in.\n"
            "Please run 'apheris login' in the CLI or call 'apheris_auth.login()'."
        )

    with credentials_file.open() as f:
        return json.load(f)


def save_session_info(
    session_info: dict, credentials_file: Path = settings.CREDENTIALS_FILE
) -> None:
    """
    Save `session_info` on the user's machine.
    """
    logger.debug("saving to file: %s", credentials_file)
    credentials_file.parent.resolve().mkdir(parents=True, exist_ok=True)
    with credentials_file.open("w") as f:
        json.dump(session_info, f, indent=4)


def build_headers():
    """Get session headers."""
    from .. import __version__

    return {
        "User-Agent": f"Apheris Auth/{__version__} (SSO)",
        "Accept": "application/json, */*",
    }
