"""Tests for the provider abstraction contracts."""

from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any, Mapping

from keysec.providers.crypto.crypto_provider import CryptoProvider
from keysec.providers.provider import Provider
from keysec.providers.service.service_provider import ServiceProvider


class TestServiceProvider(ServiceProvider):
    def get_secret(self, secret: str) -> str:
        return f"value:{secret}"


class TestCryptoProvider(CryptoProvider):
    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        return plaintext

    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        return ciphertext

    def generate_key(self, output_path: str | Path | None = None) -> str:
        return str(output_path or "test.key")


class ProviderContractTests(unittest.TestCase):
    def test_service_and_crypto_contracts_share_provider_base(self) -> None:
        self.assertTrue(issubclass(ServiceProvider, Provider))
        self.assertTrue(issubclass(CryptoProvider, Provider))
        self.assertTrue(issubclass(TestServiceProvider, Provider))
        self.assertTrue(issubclass(TestCryptoProvider, Provider))

    def test_category_operations_are_separate(self) -> None:
        self.assertTrue(hasattr(ServiceProvider, "get_secret"))
        self.assertFalse(hasattr(ServiceProvider, "encrypt"))
        self.assertFalse(hasattr(ServiceProvider, "decrypt"))
        self.assertTrue(hasattr(CryptoProvider, "encrypt"))
        self.assertTrue(hasattr(CryptoProvider, "decrypt"))
        self.assertFalse(hasattr(CryptoProvider, "get_secret"))

    def test_provider_keeps_identity_and_settings_read_only(self) -> None:
        source_settings: dict[str, Any] = {"region": "west"}
        provider = TestServiceProvider("vault", source_settings)
        source_settings["region"] = "east"

        self.assertEqual(provider.name, "vault")
        self.assertEqual(provider.settings["region"], "west")
        with self.assertRaises(TypeError):
            provider.settings["region"] = "north"  # type: ignore[index]

    def test_provider_contract_methods(self) -> None:
        service = TestServiceProvider("test-service", {})
        crypto = TestCryptoProvider("test-crypto", {})

        self.assertEqual(service.get_secret("item"), "value:item")
        self.assertEqual(crypto.encrypt("text"), "text")
        self.assertEqual(crypto.decrypt("text"), "text")


if __name__ == "__main__":
    unittest.main()
