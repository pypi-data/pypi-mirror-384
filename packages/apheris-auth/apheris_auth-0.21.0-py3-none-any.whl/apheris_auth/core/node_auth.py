import json
from base64 import b64encode
from typing import Union

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ..config import LoginType, settings
from .session import save_session_info
from .sso_helper import get_node_session


def load_pem_public_key(public_key_pem: Union[bytes, str]) -> rsa.RSAPublicKey:
    """Load public key"""
    if isinstance(public_key_pem, str):
        public_key_pem = public_key_pem.encode("utf-8")

    return serialization.load_pem_public_key(public_key_pem, backend=default_backend())


def fernet_encryption(message: bytes, key: bytes) -> bytes:
    """Ciphers the message using a fernet key."""
    f = Fernet(key)
    return f.encrypt(message)


def rsa_encryption(message: bytes, public_key: rsa.RSAPublicKey) -> bytes:
    """Ciphers the message using the RSA public key."""
    return public_key.encrypt(
        message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def build_node_auth_payload(
    key: bytes, public_key: rsa.RSAPublicKey, node_token: str
) -> dict:
    """Builds the node authentication payload.

    Schema:
    - key: fernet key ciphered with the RSA public key and base64 formatted
    - access_token: node access token ciphered with the fernet key and base64 formatted
    """
    return {
        "key": b64encode(rsa_encryption(key, public_key)).decode("utf-8"),
        "access_token": b64encode(
            fernet_encryption(node_token.encode("utf-8"), key)
        ).decode("utf-8"),
    }


def build_all_nodes_auth_payload(nodes: dict) -> str:
    """Builds the auth payload for all nodes."""
    # this is only supported when using the SSO session
    if settings.LOGIN_TYPE == LoginType.LEGACY:
        return ""

    node_oauth2_session, _ = get_node_session()
    node_access_token = node_oauth2_session.token["access_token"]
    node_encrypted_tokens = {}
    m2m_enabled = settings.m2m_enabled()

    if settings.AUTH0_ALWAYS_REFRESH_NODE_TOKEN and not m2m_enabled:
        # Note: refreshing a token will revoke the existing one
        # this is a setting in the Auth0 Node App.
        fresh_token = node_oauth2_session.refresh_token(
            token_url=settings.AUTH0_TOKEN_ENDPOINT
        )
        save_session_info(fresh_token, credentials_file=settings.NODE_CREDENTIALS_FILE)

        node_access_token = fresh_token["access_token"]
    elif m2m_enabled:
        # this will refresh the token if expired, and update the credentials file
        node_oauth2_session.ensure_active_token(node_oauth2_session.token)
        node_access_token = node_oauth2_session.token["access_token"]

    for node_id, public_key_pem in nodes.items():
        symmetric_key = Fernet.generate_key()
        public_key = load_pem_public_key(public_key_pem)

        node_encrypted_tokens[node_id] = build_node_auth_payload(
            symmetric_key, public_key, node_access_token
        )

    return b64encode(json.dumps(node_encrypted_tokens).encode("utf-8")).decode("utf-8")
