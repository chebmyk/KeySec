"""Tests for in-process crypto-provider registration."""

from __future__ import annotations

import unittest
from pathlib import Path

from keysec.config import ProviderConfig, ProviderGroupConfig
from keysec.providers.crypto.crypto_provider import CryptoProvider
from keysec.providers.crypto.crypto_provider_registry import (
    CryptoProviderRegistry,
    crypto_provider_registry,
    register_crypto_provider,
)


class TestTextCryptoProvider(CryptoProvider):
    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        return self.wrap_ciphertext(f"encrypted:{self.name}:{plaintext}")

    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        ciphertext = self.unwrap_ciphertext(ciphertext)
        return ciphertext.removeprefix(f"encrypted:{self.name}:")

    def generate_key(self, output_path: str | Path | None = None) -> str:
        return str(output_path or self.settings.get("key_file", "test.key"))


class CryptoRegistryTests(unittest.TestCase):
    def test_creates_provider_selected_by_name(self) -> None:
        group = ProviderGroupConfig(
            default="default",
            providers={
                "default": ProviderConfig("default", "text-test", {}),
                "alternate": ProviderConfig("alternate", "text-test", {}),
            },
        )
        registry = CryptoProviderRegistry()
        registry.register("text-test", TestTextCryptoProvider)

        provider = registry.create(group.select("alternate"))

        self.assertEqual(provider.name, "alternate")
        ciphertext = provider.encrypt("data")
        self.assertEqual(ciphertext, "ENC(encrypted:alternate:data)")
        self.assertEqual(provider.decrypt(ciphertext), "data")

    def test_uses_configured_default_provider(self) -> None:
        group = ProviderGroupConfig(
            default="default",
            providers={"default": ProviderConfig("default", "text-test", {})},
        )
        registry = CryptoProviderRegistry()
        registry.register("text-test", TestTextCryptoProvider)

        provider = registry.create(group.select(None))

        self.assertEqual(provider.name, "default")

    def test_rejects_duplicate_implementation_type(self) -> None:
        registry = CryptoProviderRegistry()
        registry.register("text-test", TestTextCryptoProvider)

        with self.assertRaisesRegex(ValueError, "already registered"):
            registry.register("text-test", TestTextCryptoProvider)

    def test_public_registration_function_supports_configured_provider(self) -> None:
        implementation_type = "documented-test-crypto"
        register_crypto_provider(implementation_type, TestTextCryptoProvider)
        config = ProviderConfig("custom", implementation_type, {})

        provider = crypto_provider_registry.create(config)

        self.assertEqual(provider.encrypt("data"), "ENC(encrypted:custom:data)")


if __name__ == "__main__":
    unittest.main()
