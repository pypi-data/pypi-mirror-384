"""
License validation and management for EasyRunner CLI.

This module handles JWT-based license validation with cryptographic signatures.
License enforcement is CLIENT-side only - the easyrunner library remains license-agnostic.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import jwt

# Embedded public key for license verification
# This is the PUBLIC key - it's safe to embed in the code
# The corresponding PRIVATE key is kept secret and used to generate licenses
# PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
# MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAy8Dbv8prpJ/0kKhlGeJY
# ozo2t60EG8EocLo8nLMI6UaVLKJRWL7cT6A0p+0hGJmLEm5u4rJKDVLu3RqzC3VZ
# nlU8y1hRu6h0G6xD9t9YjdGAqKhXCRWfE6DGTk5mQIKdgJdQEaE9vLBQYjGZW+GA
# e5rBVaGPvUxMLFCVF6vvF7dJtBIqXKmPzCDbZyMGiL0r3vOBjf0hRLBZmMFT5HlR
# AxJF5lJqbFLVvHWBMHbCQsGDEGMQHON7qJCvLn6eDmcEMTgT3qABFCDGE0OgHNvW
# HUqQJGXc4XRGAVvLHXVNy2x7fPXQJd0kQhRQJHnKgVg8VU3NtpFGRLvLJJh3H4M+
# YQIDAQAB
# -----END PUBLIC KEY-----"""

# Embedded public key for license verification
# This is the PUBLIC key - it's safe to embed in the code
# The corresponding PRIVATE key is kept secret and used to generate licenses
PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAtXVk0wCHCZyu6iXl6Q0j
bM9KQ0J/TChJekEYHjemAerYOk/hVavNBCl0LsenM4zJAD9qwLjNr3H79xIazJ79
5jtUzvwFmfkQ4M035wlA5zEL12DzaBkQxMCBqYqpXr9dSEQaSxEHa2Gx/2UgEdRJ
IRBZrHtEwE3Yh6+JcO4FRIbCgrq32+hOWYMikwnzAJC6rJMldiSEueZXKnSYjhDk
gOjTk5/TnELToLIQ1SJLTSKoPa2KzkIZevaOAoqd2FsmsUKDjE6twDGWCgKszbcC
MMSHNPTySCXNqnnskZ29kl4jEFaQbxJ41HsdhARjWGLArujzMfOjG0kQrXBShE1V
XQIDAQAB
-----END PUBLIC KEY-----"""


@dataclass
class LicenseInfo:
    """Information extracted from a valid license."""

    customer_email: str
    server_limit: int
    license_type: str
    issued_at: datetime
    updates_until: datetime
    license_id: str
    is_update_period_valid: bool


class LicenseManager:
    """Manages license validation and installation for EasyRunner CLI."""

    def __init__(self, license_path: Optional[Path] = None):
        """
        Initialize license manager.

        Args:
            license_path: Path to license file. Defaults to ~/.easyrunner/license.jwt
        """
        if license_path is None:
            license_path = Path.home() / ".easyrunner" / "license.jwt"
        self.license_path = license_path

    def install_license(self, source_path: Path) -> LicenseInfo:
        """
        Install a license file by copying and validating it.

        Args:
            source_path: Path to the license file to install

        Returns:
            LicenseInfo object with license details

        Raises:
            ValueError: If license is invalid or signature verification fails
            FileNotFoundError: If source license file doesn't exist
        """
        if not source_path.exists():
            raise FileNotFoundError(f"License file not found: {source_path}")

        # Read and validate the license
        with open(source_path, "r") as f:
            token = f.read().strip()

        license_info = self._validate_token(token)

        # Create .easyrunner directory if it doesn't exist
        self.license_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy license to installation location
        with open(self.license_path, "w") as f:
            f.write(token)

        return license_info

    def get_license_info(self) -> Optional[LicenseInfo]:
        """
        Get information about the currently installed license.

        Returns:
            LicenseInfo object if valid license exists, None otherwise
        """
        if not self.license_path.exists():
            return None

        try:
            with open(self.license_path, "r") as f:
                token = f.read().strip()
            return self._validate_token(token)
        except Exception:
            # Invalid or corrupted license
            return None

    def validate_license(self) -> bool:
        """
        Check if a valid license is installed.

        Returns:
            True if valid license exists, False otherwise
        """
        return self.get_license_info() is not None

    def _validate_token(self, token: str) -> LicenseInfo:
        """
        Validate a JWT license token.

        Args:
            token: JWT token string

        Returns:
            LicenseInfo object with license details

        Raises:
            ValueError: If token is invalid or signature verification fails
        """
        try:
            # Decode and verify signature
            # Note: We set verify_exp=False because we want to allow usage
            # even after update period expires (perpetual license)
            payload = jwt.decode(
                token,
                PUBLIC_KEY_PEM,
                algorithms=["RS256"],
                options={"verify_exp": False},
            )

            # Extract required fields
            customer_email = payload.get("customer_email")
            server_limit = payload.get("server_limit")
            license_type = payload.get("license_type", "perpetual")
            iat = payload.get("iat")
            exp = payload.get("exp")
            jti = payload.get("jti")

            # Validate required fields
            if not all([customer_email, server_limit, iat, exp, jti]):
                raise ValueError("License is missing required fields")

            # Convert timestamps
            issued_at = datetime.fromtimestamp(iat, tz=timezone.utc)
            updates_until = datetime.fromtimestamp(exp, tz=timezone.utc)

            # Check if update period is still valid
            is_update_period_valid = datetime.now(timezone.utc) < updates_until

            return LicenseInfo(
                customer_email=customer_email,
                server_limit=int(server_limit),
                license_type=license_type,
                issued_at=issued_at,
                updates_until=updates_until,
                license_id=jti,
                is_update_period_valid=is_update_period_valid,
            )

        except jwt.InvalidSignatureError:
            raise ValueError(
                "License signature is invalid. The license file may have been tampered with or is not authentic."
            )
        except jwt.DecodeError:
            raise ValueError(
                "License file is corrupted or in an invalid format. Please contact support for a replacement."
            )
        except jwt.ExpiredSignatureError:
            # This shouldn't happen since we set verify_exp=False, but handle it anyway
            raise ValueError(
                "License token has an invalid expiration. Please contact support."
            )
        except Exception as e:
            raise ValueError(f"License validation failed: {str(e)}")

    def remove_license(self) -> bool:
        """
        Remove the installed license.

        Returns:
            True if license was removed, False if no license was installed
        """
        if self.license_path.exists():
            self.license_path.unlink()
            return True
        return False
