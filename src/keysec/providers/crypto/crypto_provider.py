"""Abstract contract for cryptography providers."""

from abc import ABC, abstractmethod
from pathlib import Path

from keysec.providers.provider import Provider


class CryptoProvider(Provider, ABC):
    """Provider contract for text encryption and binary key-file generation."""

    @abstractmethod
    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        """Encrypt a text value and return its encoded ciphertext."""

    @abstractmethod
    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        """Decrypt an encoded ciphertext and return its text value."""

    @abstractmethod
    def generate_key(self, output_path: str | Path | None = None) -> str:
        """Write a generated key to a binary file and return its path."""
