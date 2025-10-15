"""Helpers for hashing arbitrary data."""

import hashlib
import json
from typing import Any

__all__ = ("hash_data",)


def serialize_data(data: Any) -> bytes:
    """Serializes data into a bytes object.

    - If data is a string, encode it directly.
    - If data is a dictionary, use JSON with sorted keys for consistency.
    - Otherwise, try JSON serialization; if that fails, use repr().
    """
    if isinstance(data, str):
        return data.encode("utf-8")
    if isinstance(data, dict):
        return json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    try:
        # Attempt JSON serialization for other types (e.g., list, tuple)
        return json.dumps(data).encode("utf-8")
    except (TypeError, OverflowError):
        # Fallback to repr for objects that aren't JSON serializable
        return repr(data).encode("utf-8")


def hash_data(data: Any, algorithm: str = "sha512") -> str:
    """Hashes the provided data using the specified algorithm.

    Supported algorithms:
    - md5: 32 hex characters
    - sha1: 40 hex characters
    - sha256: 64 hex characters
    - blake2b: Customizable; here set to 16 bytes (32 hex characters)
    - blake2s: Customizable; here set to 16 bytes (32 hex characters)
    """
    serialized = serialize_data(data)

    if algorithm.lower() == "md5":
        hash_obj = hashlib.md5(serialized)
    elif algorithm.lower() == "sha1":
        hash_obj = hashlib.sha1(serialized)
    elif algorithm.lower() == "sha256":
        hash_obj = hashlib.sha256(serialized)
    elif algorithm.lower() == "sha512":
        hash_obj = hashlib.sha512(serialized)
    elif algorithm.lower() == "blake2b":
        # Using 16-byte digest size for a 32-character hex digest
        hash_obj = hashlib.blake2b(serialized, digest_size=16)
    elif algorithm.lower() == "blake2s":
        # Using 16-byte digest size for a 32-character hex digest
        hash_obj = hashlib.blake2s(serialized, digest_size=16)
    else:
        raise ValueError("Unsupported algorithm selected.")

    return hash_obj.hexdigest()
