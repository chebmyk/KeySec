"""Abstract contract for cryptography providers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping

from keysec.audit import AuditLogger, audit
from keysec.model.errors import ConfigurationError, CryptoError
from keysec.providers.provider import Provider


class CryptoProvider(Provider, ABC):
    """Provider contract for text encryption and binary key-file generation."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        for method_name in ("encrypt", "decrypt", "generate_key"):
            method = cls.__dict__.get(method_name)
            operation = getattr(
                getattr(CryptoProvider, method_name),
                "__audit_operation__",
            )
            if method is not None and not hasattr(method, "__audit_operation__"):
                setattr(cls, method_name, audit(operation)(method))

    def __init__(self, name: str, settings: Mapping[str, Any]) -> None:
        super().__init__(name, settings)
        self._audit_logger: AuditLogger | None = None
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
    @audit("encrypt")
    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        """Encrypt text and return ciphertext wrapped with the configured prefix."""

    @abstractmethod
    @audit("decrypt")
    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        """Decrypt wrapped or legacy unwrapped ciphertext and return its text value."""

    @abstractmethod
    @audit("key_generation")
    def generate_key(self, output_path: str | Path | None = None) -> str:
        """Write a generated key to a binary file and return its path."""
