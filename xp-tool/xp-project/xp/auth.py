"""PKCE helpers and token storage for xp.

Tokens are stored in the OS keychain when the optional `keyring`
package is available, and fall back to a 0600-permissioned file at
~/.xp/credentials.json otherwise.
"""
import base64
import hashlib
import json
import os
import secrets
import stat
from dataclasses import dataclass
from typing import Optional

from .config import get_credentials_path

try:
    import keyring
    _HAS_KEYRING = True
except ImportError:
    _HAS_KEYRING = False

_KEYRING_SERVICE = "xp-cli"
_KEYRING_USERNAME = "default"


@dataclass
class PKCEPair:
    verifier: str
    challenge: str


def generate_pkce_pair() -> PKCEPair:
    """RFC 7636 PKCE pair using S256."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PKCEPair(verifier=verifier, challenge=challenge)


def generate_state() -> str:
    """Opaque per-login value to prevent CSRF / mixed-up callbacks."""
    return secrets.token_urlsafe(24)


def save_token(token_data: dict) -> None:
    payload = json.dumps(token_data)

    if _HAS_KEYRING:
        try:
            keyring.set_password(_KEYRING_SERVICE, _KEYRING_USERNAME, payload)
            return
        except Exception:
            pass  # fall through to file storage

    path = get_credentials_path()
    path.write_text(payload)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def load_token() -> Optional[dict]:
    if _HAS_KEYRING:
        try:
            payload = keyring.get_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
            if payload:
                return json.loads(payload)
        except Exception:
            pass

    path = get_credentials_path()
    if path.exists():
        return json.loads(path.read_text())
    return None


def clear_token() -> None:
    if _HAS_KEYRING:
        try:
            keyring.delete_password(_KEYRING_SERVICE, _KEYRING_USERNAME)
        except Exception:
            pass

    path = get_credentials_path()
    if path.exists():
        path.unlink()
