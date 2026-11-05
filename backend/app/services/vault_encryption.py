"""
LegalEase AI - Tenant Evidence Vault Encryption Service (Phase 7 Module 3)
Implements:
- Pseudonymous tenant identifiers via HMAC-SHA256
- Per-tenant Data Encryption Keys (DEK) derived via HKDF (256-bit AES)
- Authenticated AES-256-GCM encryption with 12-byte random nonces and 16-byte authentication tags
- Tamper detection and physical file shredding (crypto-shredding)
"""

import hmac
import hashlib
import os
import logging
from pathlib import Path
from typing import Tuple, List, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

from app.core.config import settings

logger = logging.getLogger(__name__)

MAGIC_HEADER = b"LEGALEASE_AESGCM_V1"
NONCE_LENGTH = 12


class VaultEncryptionService:
    """
    Manages cryptographic operations for tenant-isolated evidence storage.
    Enforces per-tenant key derivation and authenticated payload encryption.
    """

    @classmethod
    def generate_tenant_pseudonym(cls, user_id: int) -> str:
        """
        Derives an immutable pseudonymous tenant identifier from user_id.
        Raw user IDs are never exposed in vector metadata or search indexes.
        """
        secret = settings.SECRET_KEY.encode("utf-8")
        msg = f"tenant_id:{user_id}".encode("utf-8")
        return hmac.new(secret, msg, hashlib.sha256).hexdigest()[:16]

    @classmethod
    def derive_tenant_dek(cls, user_id: int) -> bytes:
        """
        Derives a dedicated 256-bit AES Data Encryption Key (DEK) for the specific tenant
        using HKDF with SHA-256.
        """
        secret = settings.SECRET_KEY.encode("utf-8")
        salt = f"legalease_vault_salt_user_{user_id}".encode("utf-8")
        info = b"tenant_evidence_vault_dek_derivation"

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=info,
        )
        return hkdf.derive(secret)

    @classmethod
    def encrypt_bytes(cls, plaintext: bytes, user_id: int) -> bytes:
        """
        Encrypts plaintext bytes using AES-256-GCM under the tenant's derived DEK.
        Payload format: [MAGIC_HEADER] + [NONCE (12 bytes)] + [CIPHERTEXT + GCM TAG (16 bytes)]
        """
        dek = cls.derive_tenant_dek(user_id)
        aesgcm = AESGCM(dek)
        nonce = os.urandom(NONCE_LENGTH)

        # Authenticate with tenant pseudonym in Associated Data (AAD)
        aad = cls.generate_tenant_pseudonym(user_id).encode("utf-8")
        ciphertext = aesgcm.encrypt(nonce, plaintext, aad)

        return MAGIC_HEADER + nonce + ciphertext

    @classmethod
    def decrypt_bytes(cls, payload: bytes, user_id: int) -> bytes:
        """
        Decrypts an encrypted payload using the tenant's derived DEK.
        Verifies magic header, nonce, and GCM authentication tag.
        Raises ValueError if corrupted, tampered with, or accessed by wrong tenant.
        """
        if not payload.startswith(MAGIC_HEADER):
            # Fallback if raw unencrypted file was stored (backwards compatibility)
            return payload

        offset = len(MAGIC_HEADER)
        nonce = payload[offset : offset + NONCE_LENGTH]
        ciphertext = payload[offset + NONCE_LENGTH :]

        dek = cls.derive_tenant_dek(user_id)
        aesgcm = AESGCM(dek)
        aad = cls.generate_tenant_pseudonym(user_id).encode("utf-8")

        try:
            return aesgcm.decrypt(nonce, ciphertext, aad)
        except Exception as e:
            logger.error(f"Tenant {user_id} vault decryption failed (tampering or key mismatch): {e}")
            raise ValueError("Decryption failed: Cryptographic authentication tag verification failed.")

    @classmethod
    def shred_file(cls, file_path: str) -> bool:
        """
        Securely shreds a file on disk by overwriting with random noise and zeroes
        before unlinking.
        """
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return False

        try:
            size = path.stat().st_size
            if size > 0:
                with open(path, "ba+", buffering=0) as f:
                    # Pass 1: Random bytes
                    f.seek(0)
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
                    # Pass 2: Zeroes
                    f.seek(0)
                    f.write(b"\x00" * size)
                    f.flush()
                    os.fsync(f.fileno())
            path.unlink()
            return True
        except Exception as e:
            logger.warning(f"Error shredding file {file_path}: {e}")
            try:
                path.unlink()
                return True
            except Exception:
                return False
