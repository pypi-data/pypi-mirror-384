"""Token management for the VCP CLI."""

import json
import os
from pathlib import Path
from typing import Optional

TOKEN_FILE = Path.home() / ".vcp" / "token.json"


def save_token(token: str) -> None:
    """Save the token to the token file."""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump({"token": token}, f)


def get_token() -> Optional[str]:
    """Get the token from the token file."""
    if not TOKEN_FILE.exists():
        return None
    try:
        with open(TOKEN_FILE) as f:
            data = json.load(f)
            return data.get("token")
    except Exception:
        return None


def clear_token() -> None:
    """Clear the token file."""
    if TOKEN_FILE.exists():
        os.remove(TOKEN_FILE)
