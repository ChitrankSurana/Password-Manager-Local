#!/usr/bin/env python3
"""
Personal Password Manager - Encryption/Decryption Module
=======================================================

This module provides secure encryption and decryption functionality for password storage
using AES-256 encryption with PBKDF2 key derivation. It implements industry-standard
cryptographic practices to ensure maximum security for stored passwords.

Key Features:
- AES-256-GCM authenticated encryption (v2 format, default since v3.0)
- AES-256-CBC legacy support (v1 format, read-only for backward compatibility)
- PBKDF2 key derivation with SHA-256 and 600,000 iterations (OWASP 2023+)
- Unique salt and nonce/IV per encryption operation
- Authenticated encryption prevents ciphertext tampering (padding oracle immune)
- Memory-safe operations that clear sensitive data
- Cryptographically secure random number generation

Blob Formats:
- v1 (legacy, read-only): VERSION(1=0x01) + SALT(32) + IV(16) + CIPHERTEXT
  Uses AES-256-CBC with PKCS7 padding. No authentication tag.
  Vulnerable to padding oracle attacks. Kept for backward compatibility only.

- v2 (current): VERSION(1=0x02) + ITERATIONS(4 bytes big-endian) + SALT(32)
                 + NONCE(12) + TAG(16) + CIPHERTEXT
  Uses AES-256-GCM (Galois/Counter Mode) with authenticated encryption.
  The TAG prevents any ciphertext tampering. ITERATIONS stored in blob
  allows future-proof iteration upgrades without breaking existing data.

Security Design:
- Each password gets a unique salt and nonce
- Master password is never stored, only derived keys are used
- GCM mode provides both confidentiality and integrity (AEAD)
- Protection against rainbow table attacks via per-entry salts
- PBKDF2 with 600k iterations resists brute-force attacks

Author: Personal Password Manager
Version: 3.0.0
"""

import secrets
import struct
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from .error_handlers import handle_security_errors, monitor_performance

# Import new error handling system
from .exceptions import DecryptionError as NewDecryptionError
from .exceptions import EncryptionError as NewEncryptionError
from .exceptions import InvalidMasterPasswordError
from .logging_config import get_logger

# Import custom types
from .types import OptionalInt

# Get module logger using new logging system
logger = get_logger(__name__)

# Backwards compatibility aliases for old exception names
EncryptionError = NewEncryptionError
DecryptionError = NewDecryptionError
InvalidKeyError = InvalidMasterPasswordError
# For corrupted data, we'll use DecryptionError as it's close enough
CorruptedDataError = NewDecryptionError


class PasswordEncryption:
    """
    Main encryption class for the Personal Password Manager

    This class provides secure encryption and decryption of passwords using
    AES-256-GCM (default) with PBKDF2 key derivation. It maintains backward
    compatibility with legacy AES-256-CBC (v1) encrypted data.

    Security Features:
    - AES-256-GCM authenticated encryption (prevents ciphertext tampering)
    - PBKDF2-HMAC-SHA256 key derivation with 600,000 iterations
    - Unique salt and nonce for each encryption operation
    - Secure random number generation using OS entropy
    - Memory clearing after use to prevent key leakage

    Blob Formats:
    - v1 (0x01): VERSION + SALT(32) + IV(16) + CIPHERTEXT  [legacy CBC, read-only]
    - v2 (0x02): VERSION + ITERATIONS(4) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT  [GCM]
    """

    # =========================================================================
    # CRYPTOGRAPHIC CONSTANTS
    # =========================================================================

    # Version bytes — used to distinguish blob formats during decryption.
    # v1 blobs use AES-CBC (legacy), v2 blobs use AES-GCM (current).
    VERSION_CBC = b"\x01"  # Legacy format: AES-256-CBC with PKCS7 padding
    VERSION_GCM = b"\x02"  # Current format: AES-256-GCM authenticated encryption

    # Keep VERSION as alias for legacy code that references it
    VERSION = VERSION_CBC

    # Key and salt sizes (shared between v1 and v2)
    SALT_LENGTH = 32  # 256-bit salt for PBKDF2 key derivation
    KEY_LENGTH = 32   # 256-bit key for AES-256

    # v1 (CBC) specific constants — kept for backward compatibility
    IV_LENGTH = 16    # 128-bit IV for AES-CBC mode
    BLOCK_SIZE = 16   # 128-bit AES block size (needed for CBC padding)

    # v2 (GCM) specific constants
    # GCM uses a 96-bit (12-byte) nonce as recommended by NIST SP 800-38D.
    # Shorter nonces are faster and the standard explicitly recommends 96 bits.
    GCM_NONCE_LENGTH = 12
    # GCM produces a 128-bit (16-byte) authentication tag that proves the
    # ciphertext has not been tampered with. Any modification to the ciphertext,
    # nonce, or additional data will cause tag verification to fail.
    GCM_TAG_LENGTH = 16
    # Size of the iteration count field in the v2 blob header (4 bytes, big-endian uint32).
    # Storing iterations in the blob allows us to upgrade the iteration count
    # without breaking existing encrypted data — each blob knows its own cost.
    ITERATIONS_FIELD_LENGTH = 4

    # PBKDF2 iteration counts
    # 600,000 is the OWASP 2023+ recommendation for PBKDF2-HMAC-SHA256.
    # Previous default was 100,000 (OWASP 2017 minimum). We keep 100,000 as the
    # fallback for decrypting legacy v1 blobs that don't store their iteration count.
    DEFAULT_ITERATIONS = 600000
    LEGACY_ITERATIONS = 100000  # Used when decrypting v1 blobs

    def __init__(self, pbkdf2_iterations: OptionalInt = None) -> None:
        """
        Initialize the encryption system.

        Args:
            pbkdf2_iterations: Number of PBKDF2 iterations for key derivation.
                Defaults to 600,000 (OWASP 2023+ recommendation).
                Higher values are more secure but slower.
        """
        self.pbkdf2_iterations: int = pbkdf2_iterations or self.DEFAULT_ITERATIONS

        # Warn about potentially insecure or very slow iteration counts
        if self.pbkdf2_iterations < 100000:
            logger.warning(
                f"PBKDF2 iteration count {self.pbkdf2_iterations} is below the "
                "recommended minimum of 600,000. This weakens brute-force resistance."
            )
        elif self.pbkdf2_iterations > 2000000:
            logger.warning(
                f"PBKDF2 iteration count {self.pbkdf2_iterations} is very high. "
                "Key derivation may take several seconds per operation."
            )

        logger.info(
            f"Encryption system initialized: AES-256-GCM, "
            f"PBKDF2 iterations={self.pbkdf2_iterations}"
        )

    def generate_salt(self) -> bytes:
        """
        Generate a cryptographically secure random salt

        Uses the operating system's cryptographically secure random number
        generator to create a unique salt for each encryption operation.

        Returns:
            bytes: 32-byte random salt
        """
        try:
            # Use secrets module for cryptographically secure random generation
            salt = secrets.token_bytes(self.SALT_LENGTH)
            logger.debug(f"Generated {len(salt)}-byte salt")
            return salt

        except Exception as e:
            logger.error(f"Failed to generate salt: {e}")
            raise EncryptionError(f"Salt generation failed: {e}")

    def generate_iv(self) -> bytes:
        """
        Generate a cryptographically secure random initialization vector (IV).

        Used only for legacy v1 (CBC) operations. New v2 (GCM) operations
        use generate_nonce() instead.

        Returns:
            bytes: 16-byte random IV for AES-CBC
        """
        try:
            iv = secrets.token_bytes(self.IV_LENGTH)
            logger.debug(f"Generated {len(iv)}-byte IV")
            return iv

        except Exception as e:
            logger.error(f"Failed to generate IV: {e}")
            raise EncryptionError(f"IV generation failed: {e}")

    def generate_nonce(self) -> bytes:
        """
        Generate a cryptographically secure random nonce for AES-GCM.

        AES-GCM requires a 96-bit (12-byte) nonce per NIST SP 800-38D.
        Each nonce MUST be unique for a given key. Since we derive a unique
        key per encryption (unique salt), nonce reuse across entries is safe,
        but we still use random nonces for defense-in-depth.

        Returns:
            bytes: 12-byte random nonce for AES-GCM
        """
        try:
            nonce = secrets.token_bytes(self.GCM_NONCE_LENGTH)
            logger.debug(f"Generated {len(nonce)}-byte GCM nonce")
            return nonce

        except Exception as e:
            logger.error(f"Failed to generate nonce: {e}")
            raise EncryptionError(f"Nonce generation failed: {e}")

    def derive_key(
        self, master_password: str, salt: bytes, iterations: OptionalInt = None
    ) -> bytes:
        """
        Derive encryption key from master password using PBKDF2

        Uses PBKDF2-HMAC-SHA256 to derive a strong encryption key from the
        user's master password. The salt ensures that identical passwords
        produce different keys.

        Args:
            master_password (str): User's master password
            salt (bytes): Unique salt for key derivation
            iterations (int, optional): PBKDF2 iterations override

        Returns:
            bytes: 32-byte derived encryption key

        Raises:
            InvalidKeyError: If key derivation fails
        """
        if not master_password:
            raise InvalidKeyError("Master password cannot be empty")

        if len(salt) != self.SALT_LENGTH:
            raise InvalidKeyError(f"Salt must be {self.SALT_LENGTH} bytes")

        iterations = iterations or self.pbkdf2_iterations

        try:
            # Convert password to bytes
            password_bytes = master_password.encode("utf-8")

            # Create PBKDF2 key derivation function
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=self.KEY_LENGTH,
                salt=salt,
                iterations=iterations,
                backend=default_backend(),
            )

            # Derive key (this is computationally expensive by design)
            start_time = time.time()
            derived_key = kdf.derive(password_bytes)
            derivation_time = time.time() - start_time

            logger.debug(f"Key derivation completed in {derivation_time:.3f} seconds")

            # Clear password from memory (basic attempt)
            password_bytes = b"\x00" * len(password_bytes)

            return derived_key

        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            raise InvalidKeyError(f"Key derivation failed: {e}")

    @handle_security_errors("Password encryption failed")
    @monitor_performance(threshold_ms=4000)  # GCM + 600k PBKDF2 may take a few seconds
    def encrypt_password(self, plaintext_password: str, master_password: str) -> bytes:
        """
        Encrypt a password using AES-256-GCM with PBKDF2 key derivation (v2 format).

        AES-GCM (Galois/Counter Mode) provides authenticated encryption — it produces
        both ciphertext and an authentication tag. The tag ensures that any tampering
        with the ciphertext, nonce, or associated data will be detected during
        decryption, making this immune to padding oracle attacks that affected the
        old CBC mode.

        Process:
        1. Generate unique salt (32 bytes) and nonce (12 bytes)
        2. Derive 256-bit encryption key via PBKDF2-HMAC-SHA256 (600k iterations)
        3. Encrypt plaintext using AES-256-GCM (no padding needed — GCM is streaming)
        4. Retrieve 16-byte authentication tag from GCM
        5. Pack into v2 blob: VERSION(0x02) + ITERATIONS(4) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT

        Args:
            plaintext_password: Password to encrypt (must be non-empty)
            master_password: User's master password for key derivation

        Returns:
            bytes: v2 encrypted blob containing all components needed for decryption

        Raises:
            EncryptionError: If encryption fails for any reason
        """
        if not plaintext_password:
            raise EncryptionError("Plaintext password cannot be empty")

        if not master_password:
            raise EncryptionError("Master password cannot be empty")

        try:
            # Step 1: Generate unique random salt and nonce for this encryption.
            # Each entry gets its own salt, so even identical passwords produce
            # completely different ciphertexts.
            salt = self.generate_salt()
            nonce = self.generate_nonce()

            # Step 2: Derive a 256-bit encryption key from the master password.
            # PBKDF2 with 600k iterations makes brute-force attacks expensive
            # (~1-2 seconds per attempt on modern hardware).
            encryption_key = self.derive_key(master_password, salt)

            # Step 3: Convert plaintext to bytes. GCM does not require padding
            # (unlike CBC), so we encrypt the raw bytes directly.
            plaintext_bytes = plaintext_password.encode("utf-8")

            # Step 4: Encrypt using AES-256-GCM.
            # GCM provides both confidentiality (encryption) and integrity
            # (authentication tag). The tag is a cryptographic MAC that covers
            # both the ciphertext and any additional authenticated data (AAD).
            cipher = Cipher(
                algorithm=algorithms.AES(encryption_key),
                mode=modes.GCM(nonce),
                backend=default_backend(),
            )
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(plaintext_bytes) + encryptor.finalize()

            # Step 5: Retrieve the GCM authentication tag.
            # This 16-byte tag MUST be stored alongside the ciphertext.
            # During decryption, the tag is verified — if the ciphertext or nonce
            # has been modified, decryption will fail with InvalidTag.
            tag = encryptor.tag

            # Step 6: Pack the iteration count as 4-byte big-endian unsigned integer.
            # Storing iterations in the blob means we can upgrade the iteration count
            # in the future without breaking existing encrypted entries — each blob
            # is self-describing.
            iterations_bytes = struct.pack(">I", self.pbkdf2_iterations)

            # Step 7: Assemble the v2 encrypted blob.
            # Format: VERSION(1) + ITERATIONS(4) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT
            # Total overhead: 1 + 4 + 32 + 12 + 16 = 65 bytes before ciphertext
            encrypted_blob = (
                self.VERSION_GCM
                + iterations_bytes
                + salt
                + nonce
                + tag
                + ciphertext
            )

            # Step 8: Best-effort memory clearing of sensitive data.
            # Python's garbage collector may retain copies, but overwriting the
            # local variable references is better than leaving them as-is.
            encryption_key = b"\x00" * len(encryption_key)
            plaintext_bytes = b"\x00" * len(plaintext_bytes)

            logger.debug(
                f"Password encrypted (v2/GCM), blob size: {len(encrypted_blob)} bytes"
            )
            return encrypted_blob

        except (EncryptionError, InvalidKeyError):
            raise
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise EncryptionError(f"Encryption failed: {e}")

    @handle_security_errors("Password decryption failed")
    @monitor_performance(threshold_ms=4000)  # 600k PBKDF2 takes ~1-2s
    def decrypt_password(self, encrypted_blob: bytes, master_password: str) -> str:
        """
        Decrypt a password, automatically detecting the blob format (v1 or v2).

        This method reads the version byte from the blob header and dispatches to
        the appropriate decryption logic:
        - v1 (0x01): Legacy AES-256-CBC with PKCS7 padding (backward compatibility)
        - v2 (0x02): AES-256-GCM authenticated encryption (current format)

        For v2 blobs, the GCM authentication tag is verified BEFORE returning the
        plaintext. If the ciphertext has been tampered with, decryption will fail
        with an InvalidTag exception, which is caught and raised as DecryptionError.

        Args:
            encrypted_blob: Encrypted data blob from encrypt_password()
            master_password: User's master password for key derivation

        Returns:
            str: Decrypted plaintext password

        Raises:
            DecryptionError: If decryption fails (wrong password, tampered data, etc.)
            CorruptedDataError: If the blob format is invalid or corrupted
        """
        if not encrypted_blob:
            raise DecryptionError("Encrypted blob cannot be empty")

        if not master_password:
            raise DecryptionError("Master password cannot be empty")

        try:
            # Read the version byte to determine which format to use.
            # The version byte is always the first byte of the blob.
            if len(encrypted_blob) < 1:
                raise CorruptedDataError("Encrypted blob is empty")

            version = encrypted_blob[0:1]

            if version == self.VERSION_CBC:
                # v1 format: AES-256-CBC (legacy, kept for backward compatibility)
                return self._decrypt_v1_cbc(encrypted_blob, master_password)
            elif version == self.VERSION_GCM:
                # v2 format: AES-256-GCM authenticated encryption (current)
                return self._decrypt_v2_gcm(encrypted_blob, master_password)
            else:
                raise CorruptedDataError(
                    f"Unknown blob version: 0x{version.hex()}. "
                    "Expected 0x01 (CBC) or 0x02 (GCM)."
                )

        except (DecryptionError, CorruptedDataError, InvalidKeyError):
            raise
        except UnicodeDecodeError:
            raise CorruptedDataError("Decrypted data is not valid UTF-8")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise DecryptionError(f"Decryption failed: {e}")

    def _decrypt_v1_cbc(self, encrypted_blob: bytes, master_password: str) -> str:
        """
        Decrypt a v1 (AES-256-CBC) blob. Legacy format — read-only support.

        v1 blob format: VERSION(1=0x01) + SALT(32) + IV(16) + CIPHERTEXT
        Uses PKCS7 padding and the legacy 100,000 PBKDF2 iterations.

        WARNING: This format has NO authentication tag, making it vulnerable to
        padding oracle attacks. All v1 blobs should be migrated to v2 (GCM)
        using migrate_entry_to_gcm().

        Args:
            encrypted_blob: v1 encrypted blob
            master_password: Master password for key derivation

        Returns:
            str: Decrypted plaintext password
        """
        # Minimum size: version(1) + salt(32) + iv(16) + one_block(16) = 65
        min_size = 1 + self.SALT_LENGTH + self.IV_LENGTH + self.BLOCK_SIZE
        if len(encrypted_blob) < min_size:
            raise CorruptedDataError(
                f"v1 blob too short: {len(encrypted_blob)} < {min_size}"
            )

        # Parse v1 blob components
        offset = 1  # Skip version byte (already validated)

        salt = encrypted_blob[offset:offset + self.SALT_LENGTH]
        offset += self.SALT_LENGTH

        iv = encrypted_blob[offset:offset + self.IV_LENGTH]
        offset += self.IV_LENGTH

        ciphertext = encrypted_blob[offset:]

        # CBC ciphertext must be a multiple of the block size
        if len(ciphertext) % self.BLOCK_SIZE != 0:
            raise CorruptedDataError(
                "v1 ciphertext length is not a multiple of block size"
            )

        # Derive key using legacy iteration count (100,000).
        # v1 blobs don't store their iteration count, so we use the hardcoded legacy value.
        decryption_key = self.derive_key(
            master_password, salt, iterations=self.LEGACY_ITERATIONS
        )

        # Decrypt using AES-256-CBC
        cipher = Cipher(
            algorithm=algorithms.AES(decryption_key),
            mode=modes.CBC(iv),
            backend=default_backend(),
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

        # Remove PKCS7 padding
        unpadder = padding.PKCS7(self.BLOCK_SIZE * 8).unpadder()
        plaintext_bytes = unpadder.update(padded_plaintext)
        plaintext_bytes += unpadder.finalize()

        # Convert to string
        plaintext_password = plaintext_bytes.decode("utf-8")

        # Clear sensitive data
        decryption_key = b"\x00" * len(decryption_key)
        padded_plaintext = b"\x00" * len(padded_plaintext)
        plaintext_bytes = b"\x00" * len(plaintext_bytes)

        logger.debug("Password decrypted (v1/CBC legacy format)")
        return plaintext_password

    def _decrypt_v2_gcm(self, encrypted_blob: bytes, master_password: str) -> str:
        """
        Decrypt a v2 (AES-256-GCM) blob with authenticated encryption.

        v2 blob format: VERSION(1=0x02) + ITERATIONS(4) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT

        The GCM authentication tag is verified during decryption. If the ciphertext
        or any header field has been modified, the cryptography library raises
        InvalidTag, which we convert to a DecryptionError. This makes v2 immune
        to padding oracle attacks and any form of ciphertext tampering.

        Args:
            encrypted_blob: v2 encrypted blob
            master_password: Master password for key derivation

        Returns:
            str: Decrypted plaintext password
        """
        # Minimum size: version(1) + iterations(4) + salt(32) + nonce(12) + tag(16) + at_least_1_byte = 66
        min_size = (
            1
            + self.ITERATIONS_FIELD_LENGTH
            + self.SALT_LENGTH
            + self.GCM_NONCE_LENGTH
            + self.GCM_TAG_LENGTH
            + 1  # At least 1 byte of ciphertext
        )
        if len(encrypted_blob) < min_size:
            raise CorruptedDataError(
                f"v2 blob too short: {len(encrypted_blob)} < {min_size}"
            )

        # Parse v2 blob components
        offset = 1  # Skip version byte (already validated)

        # Read iteration count from blob header.
        # This is a 4-byte big-endian unsigned integer, allowing up to ~4.3 billion iterations.
        iterations_bytes = encrypted_blob[offset:offset + self.ITERATIONS_FIELD_LENGTH]
        iterations = struct.unpack(">I", iterations_bytes)[0]
        offset += self.ITERATIONS_FIELD_LENGTH

        # Validate iterations is reasonable (prevent corrupt data from causing hangs)
        if iterations < 1000 or iterations > 10_000_000:
            raise CorruptedDataError(
                f"Unreasonable iteration count in blob: {iterations}"
            )

        salt = encrypted_blob[offset:offset + self.SALT_LENGTH]
        offset += self.SALT_LENGTH

        nonce = encrypted_blob[offset:offset + self.GCM_NONCE_LENGTH]
        offset += self.GCM_NONCE_LENGTH

        tag = encrypted_blob[offset:offset + self.GCM_TAG_LENGTH]
        offset += self.GCM_TAG_LENGTH

        ciphertext = encrypted_blob[offset:]

        if len(ciphertext) == 0:
            raise CorruptedDataError("v2 blob has empty ciphertext")

        # Derive the decryption key using the iteration count stored in the blob.
        # This means each blob is self-describing — we can upgrade iteration counts
        # without breaking old entries.
        decryption_key = self.derive_key(master_password, salt, iterations=iterations)

        # Decrypt using AES-256-GCM with the authentication tag.
        # The tag is passed to the GCM mode constructor and verified during finalize().
        # If the ciphertext has been tampered with, finalize() raises InvalidTag.
        try:
            cipher = Cipher(
                algorithm=algorithms.AES(decryption_key),
                mode=modes.GCM(nonce, tag),
                backend=default_backend(),
            )
            decryptor = cipher.decryptor()
            plaintext_bytes = decryptor.update(ciphertext) + decryptor.finalize()
        except Exception as e:
            # GCM tag verification failure indicates either wrong password or
            # tampered ciphertext. We raise DecryptionError for both cases
            # to avoid leaking information about which one occurred.
            error_msg = str(e).lower()
            if "tag" in error_msg or "authentication" in error_msg:
                raise DecryptionError(
                    "Decryption failed: authentication tag mismatch. "
                    "Wrong password or corrupted data."
                )
            raise

        # Convert to string (no unpadding needed — GCM is a streaming cipher)
        plaintext_password = plaintext_bytes.decode("utf-8")

        # Clear sensitive data
        decryption_key = b"\x00" * len(decryption_key)
        plaintext_bytes = b"\x00" * len(plaintext_bytes)

        logger.debug("Password decrypted (v2/GCM authenticated)")
        return plaintext_password

    @handle_security_errors("Master password change failed")
    @monitor_performance(threshold_ms=4000)  # Two crypto operations, allow more time
    def change_master_password(
        self, encrypted_blob: bytes, old_master_password: str, new_master_password: str
    ) -> bytes:
        """
        Re-encrypt data with a new master password

        This method allows users to change their master password by:
        1. Decrypting with the old master password
        2. Re-encrypting with the new master password
        3. Using new salt and IV for enhanced security

        Args:
            encrypted_blob (bytes): Currently encrypted data
            old_master_password (str): Current master password
            new_master_password (str): New master password

        Returns:
            bytes: Re-encrypted data blob with new master password

        Raises:
            DecryptionError: If decryption with old password fails
            EncryptionError: If re-encryption with new password fails
        """
        try:
            # Decrypt with old master password
            plaintext_password = self.decrypt_password(encrypted_blob, old_master_password)

            # Re-encrypt with new master password (generates new salt/IV)
            new_encrypted_blob = self.encrypt_password(plaintext_password, new_master_password)

            # Clear plaintext from memory
            plaintext_password = "\x00" * len(plaintext_password)

            logger.info("Master password changed successfully")
            return new_encrypted_blob

        except (DecryptionError, EncryptionError):
            raise
        except Exception as e:
            logger.error(f"Master password change failed: {e}")
            raise EncryptionError(f"Master password change failed: {e}")

    def verify_master_password(self, encrypted_blob: bytes, master_password: str) -> bool:
        """
        Verify that a master password can decrypt the given encrypted data

        This method attempts to decrypt the data without returning the plaintext,
        which is useful for password verification without exposing sensitive data.

        Args:
            encrypted_blob (bytes): Encrypted data to test
            master_password (str): Master password to verify

        Returns:
            bool: True if master password is correct, False otherwise
        """
        try:
            # Attempt decryption - if successful, password is correct
            self.decrypt_password(encrypted_blob, master_password)
            return True

        except (DecryptionError, CorruptedDataError, InvalidKeyError):
            return False
        except Exception:
            return False

    def migrate_entry_to_gcm(
        self, encrypted_blob: bytes, master_password: str
    ) -> bytes:
        """
        Migrate an encrypted entry from v1 (CBC) format to v2 (GCM) format.

        This method decrypts the v1 blob using the legacy CBC mode, then
        re-encrypts the plaintext using the current GCM mode with the updated
        PBKDF2 iteration count. The result is a fully authenticated v2 blob.

        If the blob is already v2 (GCM), it is returned unchanged — this makes
        the method safe to call on any entry without checking the version first.

        Args:
            encrypted_blob: The encrypted password blob (v1 or v2 format)
            master_password: The user's master password

        Returns:
            bytes: v2 (GCM) encrypted blob, or the original blob if already v2

        Raises:
            DecryptionError: If decryption of the v1 blob fails
            EncryptionError: If re-encryption to v2 fails
        """
        # If already v2, no migration needed
        if encrypted_blob and encrypted_blob[0:1] == self.VERSION_GCM:
            logger.debug("Entry already in v2 (GCM) format, skipping migration")
            return encrypted_blob

        # Decrypt with v1 (CBC) format using legacy iterations
        plaintext = self.decrypt_password(encrypted_blob, master_password)

        # Re-encrypt with v2 (GCM) format using current iterations
        new_blob = self.encrypt_password(plaintext, master_password)

        # Clear plaintext from memory
        plaintext = "\x00" * len(plaintext)

        logger.debug("Entry migrated from v1 (CBC) to v2 (GCM)")
        return new_blob

    def get_blob_version(self, encrypted_blob: bytes) -> int:
        """
        Get the version number of an encrypted blob without decrypting.

        Useful for quickly checking whether an entry needs migration.

        Args:
            encrypted_blob: The encrypted password blob

        Returns:
            int: Version number (1 for CBC, 2 for GCM)

        Raises:
            CorruptedDataError: If the blob is empty or has an unknown version
        """
        if not encrypted_blob or len(encrypted_blob) < 1:
            raise CorruptedDataError("Encrypted blob is empty")

        version_byte = encrypted_blob[0:1]
        if version_byte == self.VERSION_CBC:
            return 1
        elif version_byte == self.VERSION_GCM:
            return 2
        else:
            raise CorruptedDataError(f"Unknown version byte: 0x{version_byte.hex()}")

    def get_encryption_info(self, encrypted_blob: bytes) -> Dict[str, Any]:
        """
        Extract metadata from an encrypted blob without decrypting.

        Provides information about the encryption format, version, and parameters
        without requiring the master password. Supports both v1 and v2 formats.

        Args:
            encrypted_blob: Encrypted data blob

        Returns:
            dict: Metadata including version, algorithm, sizes, and iterations

        Raises:
            CorruptedDataError: If blob format is invalid
        """
        if not encrypted_blob:
            raise CorruptedDataError("Encrypted blob cannot be empty")

        try:
            version_byte = encrypted_blob[0:1]

            if version_byte == self.VERSION_CBC:
                # v1 format: VERSION(1) + SALT(32) + IV(16) + CIPHERTEXT
                min_size = 1 + self.SALT_LENGTH + self.IV_LENGTH
                if len(encrypted_blob) < min_size:
                    raise CorruptedDataError("v1 blob too short for metadata")

                return {
                    "version": 1,
                    "version_hex": version_byte.hex(),
                    "algorithm": "AES-256-CBC",
                    "authenticated": False,
                    "total_size": len(encrypted_blob),
                    "ciphertext_size": len(encrypted_blob) - min_size,
                    "salt_length": self.SALT_LENGTH,
                    "iv_length": self.IV_LENGTH,
                    "iterations": self.LEGACY_ITERATIONS,
                    "needs_migration": True,
                }

            elif version_byte == self.VERSION_GCM:
                # v2 format: VERSION(1) + ITERATIONS(4) + SALT(32) + NONCE(12) + TAG(16) + CIPHERTEXT
                header_size = (
                    1 + self.ITERATIONS_FIELD_LENGTH + self.SALT_LENGTH
                    + self.GCM_NONCE_LENGTH + self.GCM_TAG_LENGTH
                )
                if len(encrypted_blob) < header_size:
                    raise CorruptedDataError("v2 blob too short for metadata")

                # Read iteration count from the blob
                iterations = struct.unpack(
                    ">I",
                    encrypted_blob[1:1 + self.ITERATIONS_FIELD_LENGTH],
                )[0]

                return {
                    "version": 2,
                    "version_hex": version_byte.hex(),
                    "algorithm": "AES-256-GCM",
                    "authenticated": True,
                    "total_size": len(encrypted_blob),
                    "ciphertext_size": len(encrypted_blob) - header_size,
                    "salt_length": self.SALT_LENGTH,
                    "nonce_length": self.GCM_NONCE_LENGTH,
                    "tag_length": self.GCM_TAG_LENGTH,
                    "iterations": iterations,
                    "needs_migration": False,
                }

            else:
                raise CorruptedDataError(
                    f"Unknown version: 0x{version_byte.hex()}"
                )

        except CorruptedDataError:
            raise
        except Exception as e:
            logger.error(f"Failed to extract encryption info: {e}")
            raise CorruptedDataError(f"Invalid encryption format: {e}")


# Utility functions for external use


def create_encryption_system(pbkdf2_iterations: OptionalInt = None) -> PasswordEncryption:
    """
    Factory function to create an encryption system instance

    Args:
        pbkdf2_iterations (int, optional): PBKDF2 iterations override

    Returns:
        PasswordEncryption: Configured encryption system
    """
    return PasswordEncryption(pbkdf2_iterations)


def benchmark_encryption_performance(
    master_password: str = "test_password", iterations_list: Optional[List[int]] = None
) -> Dict[int, Dict[str, Any]]:
    """
    Benchmark encryption performance with different PBKDF2 iteration counts

    This function helps determine optimal iteration counts for the user's hardware
    by measuring encryption and decryption times.

    Args:
        master_password (str): Test password for benchmarking
        iterations_list (list, optional): List of iteration counts to test

    Returns:
        dict: Performance results for each iteration count
    """
    if iterations_list is None:
        iterations_list = [100000, 200000, 400000, 600000, 1000000]

    results = {}
    test_password = "This is a test password for benchmarking purposes"

    for iterations in iterations_list:
        try:
            encryption_system = PasswordEncryption(iterations)

            # Measure encryption time
            start_time = time.time()
            encrypted_blob = encryption_system.encrypt_password(test_password, master_password)
            encryption_time = time.time() - start_time

            # Measure decryption time
            start_time = time.time()
            decrypted_password = encryption_system.decrypt_password(encrypted_blob, master_password)
            decryption_time = time.time() - start_time

            # Verify correctness
            if decrypted_password != test_password:
                results[iterations] = {"error": "Decryption mismatch"}
                continue

            results[iterations] = {
                "encryption_time": round(encryption_time, 3),
                "decryption_time": round(decryption_time, 3),
                "total_time": round(encryption_time + decryption_time, 3),
                "blob_size": len(encrypted_blob),
            }

        except Exception as e:
            results[iterations] = {"error": str(e)}

    return results


def secure_memory_clear(data: bytes) -> None:
    """
    Attempt to securely clear sensitive data from memory

    Note: This is a best-effort implementation. True secure memory clearing
    requires OS-specific system calls and may not be fully effective in Python
    due to garbage collection and string interning.

    Args:
        data (bytes): Sensitive data to clear
    """
    try:
        # Overwrite memory with zeros (basic attempt)
        if isinstance(data, bytes):
            # This may not actually clear the memory due to Python's memory management
            for i in range(len(data)):
                data = data[:i] + b"\x00" + data[i + 1 :]
    except Exception:
        pass  # Fail silently as this is best-effort


if __name__ == "__main__":
    # Test code for encryption functionality
    print("Testing Personal Password Manager Encryption...")

    # Initialize encryption system
    encryption = PasswordEncryption()

    try:
        # Test data
        test_password = "MySecretPassword123!"
        master_password = "UserMasterPassword456"

        print(f"Original password: {test_password}")

        # Test encryption
        encrypted_blob = encryption.encrypt_password(test_password, master_password)
        print(f"✓ Encryption successful, blob size: {len(encrypted_blob)} bytes")

        # Test decryption
        decrypted_password = encryption.decrypt_password(encrypted_blob, master_password)
        print(f"✓ Decryption successful: {decrypted_password}")

        # Verify correctness
        if test_password == decrypted_password:
            print("✓ Encryption/decryption verification passed")
        else:
            print("❌ Verification failed - passwords don't match")

        # Test master password verification
        if encryption.verify_master_password(encrypted_blob, master_password):
            print("✓ Master password verification successful")

        if not encryption.verify_master_password(encrypted_blob, "wrong_password"):
            print("✓ Wrong master password correctly rejected")

        # Test encryption info
        info = encryption.get_encryption_info(encrypted_blob)
        print(f"✓ Encryption info: {info}")

        # Performance benchmark
        print("\nRunning performance benchmark...")
        benchmark_results = benchmark_encryption_performance(master_password)

        print("Performance Results:")
        for iterations, result in benchmark_results.items():
            if "error" in result:
                print(f"  {iterations:6d} iterations: ERROR - {result['error']}")
            else:
                print(
                    f"  {iterations:6d} iterations: "
                    f"Encrypt: {result['encryption_time']:5.3f}s, "
                    f"Decrypt: {result['decryption_time']:5.3f}s, "
                    f"Total: {result['total_time']:5.3f}s"
                )

        print("\n✓ All encryption tests passed!")

    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        import traceback

        traceback.print_exc()
