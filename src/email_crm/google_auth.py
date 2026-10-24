"""Load Google OAuth credentials from an authorized-user token file.

The token file path is passed explicitly or via the ``GOOGLE_TOKEN_FILE`` environment
variable. Token files are never stored in this repository.
"""

import os
from pathlib import Path

ENV_TOKEN_FILE = "GOOGLE_TOKEN_FILE"


class GoogleAuthError(RuntimeError):
    """Raised when Google credentials or the optional Google libraries are unavailable."""


def resolve_token_path(token_file: str | None = None) -> Path:
    raw = token_file or os.environ.get(ENV_TOKEN_FILE)
    if not raw:
        raise GoogleAuthError(f"No token file given. Use --token-file or set {ENV_TOKEN_FILE}.")
    path = Path(raw).expanduser()
    if not path.is_file():
        raise GoogleAuthError(f"Token file not found: {path}")
    return path


def load_credentials(token_file: str | None = None):
    """Return refreshed ``google.oauth2.credentials.Credentials`` for the given token file."""
    try:
        from google.auth.exceptions import RefreshError
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise GoogleAuthError("Install the Google extra: pip install -e .[google]") from exc

    path = resolve_token_path(token_file)
    creds = Credentials.from_authorized_user_file(str(path))
    if not creds.valid:
        if creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError as exc:
                raise GoogleAuthError(
                    f"Google rejected the refresh token ({exc.args[0]}). The token expired or was "
                    "revoked; re-run the OAuth consent flow to create a new token file."
                ) from exc
        else:
            raise GoogleAuthError("Token is invalid and has no refresh token. Re-authenticate.")
    return creds


def build_service(api: str, version: str, token_file: str | None = None):
    """Build a Google API client (e.g. ``gmail``/``v1`` or ``sheets``/``v4``)."""
    resolve_token_path(token_file)  # fail fast with a clear message before importing Google libs
    try:
        from googleapiclient.discovery import build
    except ImportError as exc:  # pragma: no cover - depends on optional extra
        raise GoogleAuthError("Install the Google extra: pip install -e .[google]") from exc
    return build(api, version, credentials=load_credentials(token_file), cache_discovery=False)
