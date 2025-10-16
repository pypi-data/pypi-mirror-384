#!/usr/bin/env python

"""Manages API keys with secure obfuscation.

This module provides functionality to securely store and retrieve API keys. Keys are obfuscated to
avoid storing in plain text while still allowing the application to use them for API calls.
"""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from polykit import PolyEnv


class APIKeyManager:
    """Manages API keys with obfuscation to prevent casual inspection."""

    _APP_SALT = "BuRdjP7teuDnGDrsJmwjnJBYc6FHV6vRF4xi6KEJybpyTZFVuvV2W9EFrbJ6fPLb"

    @classmethod
    def get_key(cls, service: str, requires_user_key: bool = False) -> str:
        """Get API key for a service."""
        # Handle services that require a user-supplied API key first
        if requires_user_key:
            env = PolyEnv()
            var_name = f"IPLOOKER_API_KEY_{service.upper().replace('.', '')}"
            try:
                if key := env.get(var_name):
                    return key
            except (KeyError, ValueError):
                pass

            return ""

        # Load the encoded keys from file
        keys_path = Path(__file__).parent / "encoded_keys.json"
        try:
            with Path(keys_path).open(encoding="utf-8") as f:
                encoded_keys = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            encoded_keys = {}

        # Get and decode the key for the requested service
        encoded = encoded_keys.get(service, "")
        if encoded:
            return cls._decode_key(encoded, service)

        # Return empty string if no key is available
        return ""

    @classmethod
    def _decode_key(cls, encoded: str, service: str) -> str:
        """Decode an obfuscated API key."""
        try:
            # Create a service-specific derivation key
            service_key = hashlib.pbkdf2_hmac(
                "sha256", service.encode(), cls._APP_SALT.encode(), 10000
            ).hex()[:16]

            # Decode the base64 first
            decoded = base64.b64decode(encoded)

            # XOR with the service key
            result = bytearray()
            for i, byte in enumerate(decoded):
                key_byte = int(service_key[i % len(service_key)], 16)
                result.append(byte ^ key_byte)

            return result.decode("utf-8")
        except Exception:
            return ""


if __name__ == "__main__":
    service = input("Enter the service name to retrieve the API key: ")
    key = APIKeyManager.get_key(service)
    if key:
        print(f"Successfully retrieved key for {service}: {key[:3]}...{key[-3:]}")
    else:
        print(f"No key found for {service}")
