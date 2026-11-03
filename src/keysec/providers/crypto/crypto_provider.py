"""Abstract contract for cryptography providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping

from keysec.model.errors import ConfigurationError, CryptoError
from keysec.providers.provider import Provider


class CryptoProvider(Provider, ABC):
    """Provider contract for text encryption and binary key-file generation."""

    def __init__(self, name: str, settings: Mapping[str, Any]) -> None:
        super().__init__(name, settings)
        cipher_prefix = self.settings.get("cipher_prefix", "ENC")
        if not isinstance(cipher_prefix, str) or not cipher_prefix:
            raise ConfigurationError(
                "Crypto provider 'cipher_prefix' must be a non-empty string"
            )
        self._cipher_prefix = cipher_prefix

    @property
    def cipher_prefix(self) -> str:
        """Configured prefix for wrapped ciphertext."""
        return self._cipher_prefix

    def wrap_ciphertext(self, ciphertext: str) -> str:
        """Wrap encoded ciphertext using this provider's configured prefix."""
        return f"{self.cipher_prefix}({ciphertext})"

    def unwrap_ciphertext(self, ciphertext: str) -> str:
        """Remove this provider's wrapper while leaving legacy ciphertext intact."""
        wrapper = f"{self.cipher_prefix}("
        if not ciphertext.startswith(wrapper):
            return ciphertext
        if not ciphertext.endswith(")"):
            raise CryptoError("Ciphertext wrapper is malformed")
        return ciphertext[len(wrapper):-1]

    @abstractmethod
    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        """Encrypt text and return ciphertext wrapped with the configured prefix."""

    @abstractmethod
    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        """Decrypt wrapped or legacy unwrapped ciphertext and return its text value."""

    @abstractmethod
    def generate_key(self, output_path: str | Path | None = None) -> str:
        """Write a generated key to a binary file and return its path."""
