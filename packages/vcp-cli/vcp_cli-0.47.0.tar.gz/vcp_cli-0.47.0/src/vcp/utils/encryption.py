"""Encryption utilities for secure token storage."""

from pathlib import Path

from cryptography.fernet import Fernet


def get_or_create_key() -> bytes:
    """Get existing encryption key or create a new one."""
    key_file = Path.home() / ".vcp" / ".encryption_key"
    key_file.parent.mkdir(parents=True, exist_ok=True)

    if key_file.exists():
        try:
            # Read and validate existing key
            key = key_file.read_bytes()
            # Validate key format
            Fernet(key)  # This will raise an error if key is invalid
            return key
        except Exception:
            # If key is invalid, remove it and create a new one
            key_file.unlink()

    # Generate a new key
    key = Fernet.generate_key()

    # Ensure the key is properly formatted
    if not isinstance(key, bytes):
        key = key.encode("utf-8")

    # Save the key with restricted permissions
    key_file.write_bytes(key)
    key_file.chmod(0o600)  # Only owner can read/write

    return key


def encrypt(data: str) -> bytes:
    """Encrypt data using Fernet symmetric encryption."""
    key = get_or_create_key()
    f = Fernet(key)
    return f.encrypt(data.encode())


def decrypt(encrypted_data: bytes) -> str:
    """Decrypt data using Fernet symmetric encryption."""
    key = get_or_create_key()
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()
