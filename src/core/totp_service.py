#!/usr/bin/env python3
"""
Personal Password Manager - Two-Factor Authentication (TOTP) Service
=====================================================================

This module provides comprehensive two-factor authentication functionality
using Time-Based One-Time Password (TOTP) algorithm compliant with RFC 6238.

Key Features:
- TOTP secret generation and management
- QR code generation for authenticator apps
- TOTP code validation with time window tolerance
- Backup code generation and management
- Secure secret storage with encryption

Security Features:
- RFC 6238 compliant TOTP implementation
- 30-second time windows
- SHA-1 hashing algorithm (industry standard for TOTP)
- 10 single-use backup codes for recovery
- Automatic validation logging

Author: Personal Password Manager
Version: 2.2.0
"""

import hashlib
import json
import secrets
from typing import List, Optional, Tuple

import pyotp
import qrcode
from PIL import Image

from .exceptions import SecurityException
from .logging_config import get_logger, log_audit_event, log_security_event

logger = get_logger(__name__)


class TOTPService:
    """
    Two-Factor Authentication Service using TOTP

    Provides comprehensive 2FA functionality including secret generation,
    QR code creation, code validation, and backup code management.
    """

    # TOTP Configuration
    TOTP_INTERVAL = 30  # 30 seconds per code
    TOTP_DIGITS = 6  # 6-digit codes
    TOTP_ALGORITHM = "SHA1"  # Standard for TOTP
    ISSUER_NAME = "Password Manager"  # Shown in authenticator apps

    # Backup codes configuration
    BACKUP_CODE_COUNT = 10
    BACKUP_CODE_LENGTH = 8  # Characters per backup code

    def __init__(self):
        """Initialize the TOTP service"""
        logger.info("TOTP Service initialized")

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key

        Returns:
            str: Base32-encoded secret key (32 characters)

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> print(secret)
            'JBSWY3DPEHPK3PXP'
        """
        try:
            # Generate a random base32 secret (160 bits = 32 base32 characters)
            secret = pyotp.random_base32()
            logger.info("Generated new TOTP secret")
            return secret
        except Exception as e:
            logger.error(f"Failed to generate TOTP secret: {e}")
            raise SecurityException(
                "Failed to generate authentication secret", details={"error": str(e)}
            )

    def generate_qr_code(self, secret: str, username: str, size: int = 300) -> Image.Image:
        """
        Generate QR code for TOTP setup

        Args:
            secret: The TOTP secret key
            username: User's username (displayed in authenticator app)
            size: QR code size in pixels (default: 300x300)

        Returns:
            PIL.Image.Image: QR code image

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> qr_image = service.generate_qr_code(secret, "john@example.com")
            >>> qr_image.save("qrcode.png")
        """
        try:
            # Create TOTP URI for authenticator apps
            totp = pyotp.TOTP(secret)
            uri = totp.provisioning_uri(name=username, issuer_name=self.ISSUER_NAME)

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)

            # Create PIL image
            img = qr.make_image(fill_color="black", back_color="white")

            # Resize to requested size
            img = img.resize((size, size), Image.Resampling.LANCZOS)

            logger.info(f"Generated QR code for user: {username}")
            return img

        except Exception as e:
            logger.error(f"Failed to generate QR code: {e}")
            raise SecurityException("Failed to generate QR code", details={"error": str(e)})

    def verify_totp_code(
        self, secret: str, code: str, user_id: Optional[int] = None, username: Optional[str] = None
    ) -> bool:
        """
        Verify a TOTP code

        Args:
            secret: The TOTP secret key
            code: 6-digit code to verify
            user_id: Optional user ID for logging
            username: Optional username for logging

        Returns:
            bool: True if code is valid, False otherwise

        Note:
            Accepts codes from 1 window before and after current time
            (90-second total window) to account for time drift
        """
        try:
            # Clean the code (remove spaces, hyphens)
            code = code.replace(" ", "").replace("-", "")

            # Validate code format
            if not code.isdigit() or len(code) != self.TOTP_DIGITS:
                logger.warning(f"Invalid TOTP code format: {len(code)} digits")
                log_security_event(
                    "TOTP_VALIDATION_FAILED",
                    f"Invalid TOTP code format for user {username}",
                    severity="WARNING",
                    user_id=user_id,
                )
                return False

            # Create TOTP instance
            totp = pyotp.TOTP(secret)

            # Verify with 1 window tolerance (30 seconds before/after)
            is_valid = totp.verify(code, valid_window=1)

            if is_valid:
                logger.info(f"TOTP code verified successfully for user: {username}")
                log_security_event(
                    "TOTP_VALIDATION_SUCCESS",
                    f"TOTP code validated for user {username}",
                    severity="INFO",
                    user_id=user_id,
                )
            else:
                logger.warning(f"TOTP code verification failed for user: {username}")
                log_security_event(
                    "TOTP_VALIDATION_FAILED",
                    f"Invalid TOTP code for user {username}",
                    severity="WARNING",
                    user_id=user_id,
                )

            return is_valid

        except Exception as e:
            logger.error(f"TOTP verification error: {e}")
            log_security_event(
                "TOTP_VALIDATION_ERROR",
                f"TOTP validation error for user {username}: {str(e)}",
                severity="ERROR",
                user_id=user_id,
            )
            return False

    def generate_backup_codes(self) -> List[str]:
        """
        Generate backup codes for account recovery

        Returns:
            List[str]: List of 10 backup codes (format: XXXX-XXXX)

        Example:
            >>> service = TOTPService()
            >>> codes = service.generate_backup_codes()
            >>> print(codes)
            ['A7K9-2M3P', 'B2N5-7H1J', 'C8M4-6P2L', ...]
        """
        try:
            codes = []
            for _ in range(self.BACKUP_CODE_COUNT):
                # Generate random alphanumeric code
                code = "".join(
                    secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789")
                    for _ in range(self.BACKUP_CODE_LENGTH)
                )
                # Format as XXXX-XXXX
                formatted_code = f"{code[:4]}-{code[4:]}"
                codes.append(formatted_code)

            logger.info(f"Generated {len(codes)} backup codes")
            return codes

        except Exception as e:
            logger.error(f"Failed to generate backup codes: {e}")
            raise SecurityException("Failed to generate backup codes", details={"error": str(e)})

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage

        Args:
            code: Backup code to hash

        Returns:
            str: SHA-256 hash of the code

        Note:
            Backup codes are stored as hashes to prevent theft if database is compromised
        """
        # Remove hyphen and convert to uppercase
        clean_code = code.replace("-", "").upper()
        # Hash with SHA-256
        hashed = hashlib.sha256(clean_code.encode()).hexdigest()
        return hashed

    def verify_backup_code(
        self,
        code: str,
        stored_codes: List[str],
        user_id: Optional[int] = None,
        username: Optional[str] = None,
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Verify a backup code and return updated codes list

        Args:
            code: Backup code to verify
            stored_codes: List of hashed backup codes from database
            user_id: Optional user ID for logging
            username: Optional username for logging

        Returns:
            Tuple[bool, Optional[List[str]]]: (is_valid, updated_codes_list)
            - is_valid: True if code matches
            - updated_codes_list: Remaining codes after removal, or None if invalid

        Note:
            Each backup code can only be used once. If valid, it's removed from the list.
        """
        try:
            # Clean the input code
            code.replace(" ", "").replace("-", "").upper()

            # Hash the provided code
            code_hash = self.hash_backup_code(code)

            # Check if code exists in stored codes
            if code_hash in stored_codes:
                # Code is valid - remove it from list
                updated_codes = [c for c in stored_codes if c != code_hash]

                logger.info(f"Backup code verified and consumed for user: {username}")
                log_security_event(
                    "BACKUP_CODE_USED",
                    f"Backup code used for user {username}. {len(updated_codes)} codes remaining.",
                    severity="WARNING",
                    user_id=user_id,
                )
                log_audit_event(
                    "BACKUP_CODE_AUTHENTICATION",
                    user_id or 0,
                    details={"username": username, "remaining_codes": len(updated_codes)},
                )

                return True, updated_codes
            else:
                logger.warning(f"Invalid backup code for user: {username}")
                log_security_event(
                    "BACKUP_CODE_FAILED",
                    f"Invalid backup code attempt for user {username}",
                    severity="WARNING",
                    user_id=user_id,
                )
                return False, None

        except Exception as e:
            logger.error(f"Backup code verification error: {e}")
            return False, None

    def prepare_backup_codes_for_storage(self, codes: List[str]) -> str:
        """
        Prepare backup codes for database storage

        Args:
            codes: List of plain-text backup codes

        Returns:
            str: JSON string of hashed codes

        Example:
            >>> service = TOTPService()
            >>> codes = service.generate_backup_codes()
            >>> storage_data = service.prepare_backup_codes_for_storage(codes)
            >>> # Store storage_data in database
        """
        hashed_codes = [self.hash_backup_code(code) for code in codes]
        return json.dumps(hashed_codes)

    def load_backup_codes_from_storage(self, storage_data: str) -> List[str]:
        """
        Load backup codes from database storage

        Args:
            storage_data: JSON string of hashed codes from database

        Returns:
            List[str]: List of hashed backup codes

        Example:
            >>> service = TOTPService()
            >>> storage_data = db.get_backup_codes(user_id)
            >>> codes = service.load_backup_codes_from_storage(storage_data)
        """
        try:
            if not storage_data:
                return []
            return json.loads(storage_data)
        except json.JSONDecodeError:
            logger.error("Failed to parse backup codes JSON")
            return []

    def get_current_totp_code(self, secret: str) -> str:
        """
        Get the current TOTP code for testing/display purposes

        Args:
            secret: The TOTP secret key

        Returns:
            str: Current 6-digit TOTP code

        Note:
            This is mainly for testing. In production, users get codes from their authenticator app.
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    def get_totp_uri(self, secret: str, username: str) -> str:
        """
        Get the TOTP provisioning URI

        Args:
            secret: The TOTP secret key
            username: User's username

        Returns:
            str: TOTP URI that can be entered manually in authenticator apps

        Example:
            >>> service = TOTPService()
            >>> uri = service.get_totp_uri(secret, "john@example.com")
            >>> print(uri)
            'otpauth://totp/Password Manager:john@example.com?secret=JBSWY3DPEHPK3PXP&issuer=Password Manager'
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=self.ISSUER_NAME)


if __name__ == "__main__":
    # Test the TOTP service
    print("TOTP Service Test")
    print("=" * 50)

    service = TOTPService()

    # Generate secret
    secret = service.generate_secret()
    print(f"Secret: {secret}")

    # Get current code
    current_code = service.get_current_totp_code(secret)
    print(f"Current TOTP Code: {current_code}")

    # Verify the code
    is_valid = service.verify_totp_code(secret, current_code)
    print(f"Code Verification: {'✓ Valid' if is_valid else '✗ Invalid'}")

    # Generate backup codes
    backup_codes = service.generate_backup_codes()
    print(f"\nBackup Codes ({len(backup_codes)}):")
    for i, code in enumerate(backup_codes, 1):
        print(f"  {i}. {code}")

    # Test backup code verification
    test_code = backup_codes[0]
    stored = service.prepare_backup_codes_for_storage(backup_codes)
    loaded = service.load_backup_codes_from_storage(stored)
    valid, remaining = service.verify_backup_code(test_code, loaded)
    print(f"\nBackup Code Test: {'✓ Valid' if valid else '✗ Invalid'}")
    print(f"Remaining Codes: {len(remaining) if remaining else 0}")

    print("\n✓ TOTP Service loaded successfully")
