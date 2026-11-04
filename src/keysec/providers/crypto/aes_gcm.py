"""AES-256-GCM text encryption provider."""

from __future__ import annotations

import base64
import binascii
import os
from pathlib import Path
import secrets

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from keysec.model.errors import CryptoError
from keysec.providers.crypto.crypto_provider import CryptoProvider

_NONCE_LENGTH = 12
_KEY_LENGTH = 32


class AESGCMProvider(CryptoProvider):
    """Encrypts UTF-8 text with AES-256-GCM."""

    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        if not isinstance(plaintext, str):
            raise TypeError("Plaintext must be a string")
        key = self._read_key(key_file)
        nonce = os.urandom(_NONCE_LENGTH)
        encrypted = AESGCM(key).encrypt(nonce, plaintext.encode("utf-8"), None)
        encoded = base64.urlsafe_b64encode(nonce + encrypted).rstrip(b"=").decode("ascii")
        return self.wrap_ciphertext(encoded)

    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        if not isinstance(ciphertext, str):
            raise TypeError("Ciphertext must be a string")
        ciphertext = self.unwrap_ciphertext(ciphertext)
        try:
            encoded_bytes = ciphertext.encode("ascii")
            padded = encoded_bytes + b"=" * (-len(encoded_bytes) % 4)
            payload = base64.b64decode(padded, altchars=b"-_", validate=True)
        except (UnicodeEncodeError, binascii.Error, ValueError) as exc:
            raise CryptoError("Ciphertext format is unsupported or malformed") from exc

        if len(payload) < _NONCE_LENGTH + 16:
            raise CryptoError("Ciphertext format is unsupported or malformed")

        nonce = payload[:_NONCE_LENGTH]
        encrypted = payload[_NONCE_LENGTH:]
        key = self._read_key(key_file)
        try:
            plaintext = AESGCM(key).decrypt(nonce, encrypted, None)
        except InvalidTag as exc:
            raise CryptoError("Ciphertext authentication failed") from exc

        try:
            return plaintext.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CryptoError("Decrypted value is not valid UTF-8 text") from exc

    def generate_key(self, output_path: str | Path | None = None) -> str:
        configured_path = (
            output_path if output_path is not None else self.settings.get("key_file")
        )
        if not isinstance(configured_path, (str, Path)) or not str(configured_path):
            raise CryptoError("No key file path is configured")

        path = Path(configured_path).expanduser()
        key = secrets.token_bytes(_KEY_LENGTH)
        try:
            file_descriptor = os.open(
                path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )
        except FileExistsError:
            raise
        except OSError as exc:
            raise CryptoError("Unable to create crypto key file") from exc

        try:
            with os.fdopen(file_descriptor, "wb") as key_output:
                key_output.write(key)
                key_output.flush()
                os.fsync(key_output.fileno())
        except OSError as exc:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                raise CryptoError(
                    "Unable to write crypto key file or remove incomplete output"
                ) from cleanup_error
            raise CryptoError("Unable to write crypto key file") from exc

        return str(path)

    def _read_key(self, key_file: str | Path | None) -> bytes:
        configured_path = key_file if key_file is not None else self.settings.get("key_file")
        if not isinstance(configured_path, (str, Path)) or not str(configured_path):
            raise CryptoError("No key file path is configured")

        try:
            key = Path(configured_path).expanduser().read_bytes()
        except OSError as exc:
            raise CryptoError("Unable to read crypto key file") from exc

        if len(key) != _KEY_LENGTH:
            raise CryptoError("AES-256-GCM key file must contain exactly 32 bytes")
        return key
