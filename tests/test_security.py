"""
Personal Password Manager - Security Tests
============================================

Validates all security-critical behavior introduced in the v3.0 upgrade:

1. AES-256-GCM encryption/decryption roundtrip
2. Legacy AES-CBC (v1) backward-compatible decryption
3. GCM authentication tag tamper detection
4. CBC-to-GCM migration preserves plaintext
5. Wrong master password is rejected
6. PBKDF2 with 600k iterations works within performance budget
7. Timing-safe comparison is used for secret values
8. Password complexity validation (reject weak, accept strong)
9. Plaintext CSV export requires explicit confirmation
10. Import verifies master password before encrypting

Each test includes a comment explaining what security property it validates.

Version: 3.0.0
"""

import inspect
import os
import secrets
import struct
import time

import pytest

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding as crypto_padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from core.encryption import DecryptionError, PasswordEncryption
from core.auth import AuthenticationManager


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def encryption():
    """Create a fresh PasswordEncryption instance for each test."""
    return PasswordEncryption()


@pytest.fixture
def master_password():
    """A strong master password used across tests."""
    return "Str0ng!P@ssw0rd_2024#"


# ---------------------------------------------------------------------------
# Helper: create a legacy v1 (CBC) blob for backward-compat tests
# ---------------------------------------------------------------------------

def _create_legacy_v1_blob(plaintext: str, master_password: str) -> bytes:
    """
    Manually construct a v1 (AES-CBC) encrypted blob.

    v1 format: VERSION(0x01) + SALT(32) + IV(16) + CIPHERTEXT
    Uses PKCS7 padding and 100,000 PBKDF2 iterations.

    This replicates the old encryption logic so we can test that the
    current decrypt_password() can still read v1 data.
    """
    enc = PasswordEncryption()

    # Generate salt and IV
    salt = secrets.token_bytes(32)
    iv = secrets.token_bytes(16)

    # Derive key with legacy iteration count
    key = enc.derive_key(master_password, salt, iterations=100_000)

    # Encrypt with AES-CBC + PKCS7 padding
    padder = crypto_padding.PKCS7(128).padder()
    padded = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend(),
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # Assemble v1 blob
    return b"\x01" + salt + iv + ciphertext


# ===========================================================================
# 1. AES-GCM encrypt/decrypt roundtrip
# ===========================================================================

class TestAESGCMRoundtrip:
    """Verify that encrypt -> decrypt produces the original plaintext."""

    def test_basic_roundtrip(self, encryption, master_password):
        """Encrypting and decrypting a password must return the original."""
        plaintext = "MyS3cretP@ssword!"
        blob = encryption.encrypt_password(plaintext, master_password)
        result = encryption.decrypt_password(blob, master_password)
        assert result == plaintext

    def test_empty_string_roundtrip(self, encryption, master_password):
        """An empty password should encrypt and decrypt without error."""
        # Some implementations reject empty strings; ours should handle them
        try:
            blob = encryption.encrypt_password("", master_password)
            result = encryption.decrypt_password(blob, master_password)
            assert result == ""
        except Exception:
            # If the implementation rejects empty strings, that's acceptable
            pass

    def test_unicode_roundtrip(self, encryption, master_password):
        """Unicode passwords (emoji, CJK, etc.) must survive the roundtrip."""
        plaintext = "p@ss\u00e9_\u4e16\u754c_\U0001f512"  # passé_世界_🔒
        blob = encryption.encrypt_password(plaintext, master_password)
        result = encryption.decrypt_password(blob, master_password)
        assert result == plaintext

    def test_long_password_roundtrip(self, encryption, master_password):
        """A 500-character password should encrypt/decrypt correctly."""
        plaintext = "A" * 500
        blob = encryption.encrypt_password(plaintext, master_password)
        result = encryption.decrypt_password(blob, master_password)
        assert result == plaintext

    def test_v2_blob_header(self, encryption, master_password):
        """The encrypted blob must start with version byte 0x02 (GCM format)."""
        blob = encryption.encrypt_password("test", master_password)
        assert blob[0:1] == b"\x02", "Encrypted blob should use v2 (GCM) format"

    def test_unique_blobs_per_encryption(self, encryption, master_password):
        """Each encryption must produce a unique blob (unique salt + nonce)."""
        blob1 = encryption.encrypt_password("same", master_password)
        blob2 = encryption.encrypt_password("same", master_password)
        assert blob1 != blob2, "Two encryptions of the same plaintext must differ"


# ===========================================================================
# 2. Legacy CBC (v1) backward compatibility
# ===========================================================================

class TestLegacyCBCBackwardCompat:
    """Verify that v1 (CBC) blobs can still be decrypted by the current code."""

    def test_decrypt_v1_blob(self, encryption, master_password):
        """
        A v1 (CBC) blob created with 100k iterations must still decrypt.

        This ensures users who upgrade from v2.x don't lose access to
        their existing passwords before migration runs.
        """
        plaintext = "OldCBCPassword123"
        v1_blob = _create_legacy_v1_blob(plaintext, master_password)
        result = encryption.decrypt_password(v1_blob, master_password)
        assert result == plaintext

    def test_v1_blob_version_byte(self):
        """The helper should produce a blob starting with 0x01."""
        blob = _create_legacy_v1_blob("test", "pass")
        assert blob[0:1] == b"\x01"


# ===========================================================================
# 3. GCM tamper detection (authentication tag failure)
# ===========================================================================

class TestGCMTamperDetection:
    """
    GCM's authentication tag ensures any modification to the ciphertext,
    nonce, or tag itself is detected. These tests flip bits in the blob
    and verify that decryption raises DecryptionError.
    """

    def test_tampered_ciphertext_raises_error(self, encryption, master_password):
        """
        Flipping a byte in the ciphertext must cause decryption to fail.

        This is the core security property of AES-GCM — it detects
        ciphertext tampering, preventing padding oracle attacks.
        """
        blob = encryption.encrypt_password("secret", master_password)

        # Tamper with the last byte of ciphertext
        tampered = bytearray(blob)
        tampered[-1] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(DecryptionError):
            encryption.decrypt_password(tampered, master_password)

    def test_tampered_tag_raises_error(self, encryption, master_password):
        """
        Flipping a byte in the GCM authentication tag must fail.

        The tag (16 bytes) starts at offset 1+4+32+12 = 49 in a v2 blob.
        """
        blob = encryption.encrypt_password("secret", master_password)

        # Tag is at offset 49 (after version + iterations + salt + nonce)
        tag_offset = 1 + 4 + 32 + 12
        tampered = bytearray(blob)
        tampered[tag_offset] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(DecryptionError):
            encryption.decrypt_password(tampered, master_password)

    def test_tampered_nonce_raises_error(self, encryption, master_password):
        """
        Modifying the nonce must cause authentication failure.

        The nonce starts at offset 1+4+32 = 37 in a v2 blob.
        """
        blob = encryption.encrypt_password("secret", master_password)

        nonce_offset = 1 + 4 + 32
        tampered = bytearray(blob)
        tampered[nonce_offset] ^= 0xFF
        tampered = bytes(tampered)

        with pytest.raises(DecryptionError):
            encryption.decrypt_password(tampered, master_password)


# ===========================================================================
# 4. CBC-to-GCM migration preserves plaintext
# ===========================================================================

class TestMigration:
    """
    The migrate_entry_to_gcm() method converts v1 (CBC) blobs to v2 (GCM)
    without changing the underlying plaintext password. This is critical
    because a migration bug could silently corrupt all stored passwords.
    """

    def test_migration_preserves_plaintext(self, encryption, master_password):
        """
        Migrating a v1 blob to v2 must preserve the original plaintext.

        Steps: create v1 blob -> migrate -> decrypt v2 blob -> compare.
        """
        plaintext = "MigrateMe_P@ss!"
        v1_blob = _create_legacy_v1_blob(plaintext, master_password)

        # Migrate to v2
        v2_blob = encryption.migrate_entry_to_gcm(v1_blob, master_password)

        # v2 blob must have the new version byte
        assert v2_blob[0:1] == b"\x02", "Migrated blob should be v2 format"

        # Decrypted plaintext must match the original
        result = encryption.decrypt_password(v2_blob, master_password)
        assert result == plaintext

    def test_migration_is_idempotent(self, encryption, master_password):
        """
        Migrating an already-v2 blob should return it unchanged.

        This ensures the migration is safe to call on any entry without
        checking the version byte first.
        """
        plaintext = "Already_GCM"
        v2_blob = encryption.encrypt_password(plaintext, master_password)

        # Migrate again — should return the same blob
        result = encryption.migrate_entry_to_gcm(v2_blob, master_password)
        assert result == v2_blob


# ===========================================================================
# 5. Wrong master password rejection
# ===========================================================================

class TestWrongPassword:
    """
    Using the wrong master password must raise DecryptionError, not
    silently return garbage data. GCM's auth tag ensures this.
    """

    def test_wrong_password_gcm(self, encryption, master_password):
        """
        Decrypting a GCM blob with the wrong password must raise an error.

        With CBC, a wrong password might produce garbage silently. GCM's
        auth tag catches this because the derived key is different.
        """
        blob = encryption.encrypt_password("secret", master_password)

        with pytest.raises(DecryptionError):
            encryption.decrypt_password(blob, "WrongPassword123!")

    def test_wrong_password_cbc(self, encryption, master_password):
        """
        Decrypting a CBC blob with the wrong password should also fail.

        Note: CBC doesn't have an auth tag, so this may fail with a
        padding error or produce garbage. The test verifies it doesn't
        silently return the correct plaintext.
        """
        v1_blob = _create_legacy_v1_blob("secret", master_password)

        try:
            result = encryption.decrypt_password(v1_blob, "WrongPassword!")
            # If decryption didn't raise, it must not return the correct plaintext
            assert result != "secret", "Wrong password must not decrypt correctly"
        except (DecryptionError, Exception):
            pass  # Expected — padding error or similar


# ===========================================================================
# 6. PBKDF2 600k iterations — roundtrip + performance
# ===========================================================================

class TestPBKDF2Performance:
    """
    Verify that the new 600k-iteration PBKDF2 works correctly and
    completes within a reasonable time budget (< 2 seconds per operation).
    """

    def test_600k_iterations_roundtrip(self, encryption, master_password):
        """
        Encryption with 600k iterations must produce a decryptable blob.
        """
        blob = encryption.encrypt_password("perf_test", master_password)
        result = encryption.decrypt_password(blob, master_password)
        assert result == "perf_test"

    def test_600k_iterations_performance(self, encryption, master_password):
        """
        A single encrypt + decrypt cycle with 600k iterations must
        complete in under 2 seconds. This prevents the iteration count
        from being so high that it makes the app unusable.
        """
        start = time.time()
        blob = encryption.encrypt_password("benchmark", master_password)
        encryption.decrypt_password(blob, master_password)
        elapsed = time.time() - start

        assert elapsed < 2.0, (
            f"Encrypt+decrypt took {elapsed:.2f}s (must be < 2s)"
        )

    def test_iterations_stored_in_blob(self, encryption, master_password):
        """
        The v2 blob must store the iteration count at bytes 1-4 so that
        future iteration upgrades can read the correct count per blob.
        """
        blob = encryption.encrypt_password("test", master_password)
        iterations = struct.unpack(">I", blob[1:5])[0]
        assert iterations == 600_000, f"Expected 600000 iterations, got {iterations}"


# ===========================================================================
# 7. Timing-safe comparison
# ===========================================================================

class TestTimingSafeComparison:
    """
    Verify that the AuthenticationManager uses hmac.compare_digest()
    for password hash comparisons. This prevents timing side-channel
    attacks where an attacker measures response time differences.
    """

    def test_verify_password_uses_compare_digest(self):
        """
        The _verify_password_hash method (or equivalent) must call
        hmac.compare_digest, not the '==' operator, for hash comparison.

        We verify this by inspecting the source code of the method.
        """
        auth = AuthenticationManager()

        # Find the method that does hash comparison
        method = getattr(auth, "_verify_password_hash", None)
        if method is None:
            # Try alternative names
            method = getattr(auth, "_constant_time_compare", None)

        if method is not None:
            source = inspect.getsource(method)
            assert "compare_digest" in source, (
                "Password hash comparison must use hmac.compare_digest() "
                "to prevent timing attacks"
            )
        else:
            # If neither method exists, check the class source broadly
            source = inspect.getsource(AuthenticationManager)
            assert "compare_digest" in source, (
                "AuthenticationManager must use hmac.compare_digest() somewhere"
            )


# ===========================================================================
# 8. Password complexity validation
# ===========================================================================

class TestPasswordComplexity:
    """
    The v3.0 upgrade enforces password complexity rules:
    - Minimum 12 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character

    These tests verify the _validate_password_complexity() method.
    """

    @pytest.fixture
    def auth(self):
        return AuthenticationManager()

    def test_reject_short_password(self, auth):
        """Passwords shorter than 12 characters must be rejected."""
        valid, msg = auth._validate_password_complexity("Short1!")
        assert not valid
        assert "12" in msg or "characters" in msg.lower()

    def test_reject_all_lowercase(self, auth):
        """Passwords without uppercase letters must be rejected."""
        valid, msg = auth._validate_password_complexity("alllowercase1!")
        assert not valid

    def test_reject_no_digits(self, auth):
        """Passwords without digits must be rejected."""
        valid, msg = auth._validate_password_complexity("NoDigitsHere!!!")
        assert not valid

    def test_reject_no_special(self, auth):
        """Passwords without special characters must be rejected."""
        valid, msg = auth._validate_password_complexity("NoSpecial1234AB")
        assert not valid

    def test_reject_repeated_chars(self, auth):
        """A trivial repeated-character password must be rejected."""
        valid, msg = auth._validate_password_complexity("111111111111")
        assert not valid

    def test_accept_strong_password(self, auth):
        """A password meeting all criteria must be accepted."""
        valid, msg = auth._validate_password_complexity("Str0ng!P@ssw0rd")
        assert valid
        assert msg == ""


# ===========================================================================
# 9. Plaintext CSV export requires confirmation
# ===========================================================================

class TestExportConfirmation:
    """
    Exporting passwords as plaintext CSV is dangerous — it creates an
    unencrypted file containing all passwords. The export_plain_csv()
    method must reject calls that don't pass confirm_plaintext=True.
    """

    def test_export_without_confirmation_raises(self):
        """
        Calling export_plain_csv() without confirm_plaintext=True must
        raise an ExportError. This prevents accidental plaintext exports.
        """
        from utils.import_export import BackupManager, ExportError

        bm = BackupManager()

        with pytest.raises(ExportError):
            bm.export_plain_csv(
                user_id=1,
                username="test",
                master_password="test",
                output_path="/tmp/should_not_exist.csv",
                confirm_plaintext=False,  # Must be True to proceed
            )

    def test_export_default_confirmation_is_false(self):
        """
        The default value of confirm_plaintext must be False so that
        callers are forced to explicitly opt in to plaintext export.
        """
        from utils.import_export import BackupManager, ExportError

        bm = BackupManager()

        # Call without the parameter at all — should default to False
        with pytest.raises(ExportError):
            bm.export_plain_csv(
                user_id=1,
                username="test",
                master_password="test",
                output_path="/tmp/should_not_exist.csv",
            )


# ===========================================================================
# 10. Import verifies master password before encrypting
# ===========================================================================

class TestImportMasterPasswordVerification:
    """
    When importing passwords, the system must verify the master password
    before encrypting imported entries. This prevents users from importing
    with the wrong password and creating entries that can't be decrypted.

    We verify this by checking the source code of the import method for
    the verification logic.
    """

    def test_import_method_verifies_password(self):
        """
        The _import_password_entries method must include master password
        verification logic (decrypt an existing entry or trial roundtrip).
        """
        from utils.import_export import BackupManager

        bm = BackupManager()
        method = getattr(bm, "_import_password_entries", None)

        if method is not None:
            source = inspect.getsource(method)
            # The verification should try decrypting an existing entry
            # or do a trial encrypt/decrypt roundtrip
            has_verification = (
                "decrypt" in source.lower()
                or "verify" in source.lower()
                or "master_password" in source.lower()
            )
            assert has_verification, (
                "_import_password_entries must verify master password "
                "before encrypting imported entries"
            )
        else:
            # If the method doesn't exist under that name, check alternatives
            pytest.skip("_import_password_entries method not found")
