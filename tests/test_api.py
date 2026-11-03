"""Tests for the public KeySec facade."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from keysec import KeySec
from keysec.model.errors import ConfigurationError, SecretRetrievalError
from keysec.model import KeySec as ModelKeySec
from keysec.providers.crypto.crypto_provider import CryptoProvider
from keysec.providers.crypto.crypto_provider_registry import register_crypto_provider
from keysec.providers.service.azure_key_vault import AzureKeyVaultProvider
from keysec.providers.service.service_provider import ServiceProvider
from keysec.providers.service.service_provider_registry import register_service_provider


class APIEchoServiceProvider(ServiceProvider):
    calls: list[str] = []

    def get_secret(self, secret: str) -> str:
        self.calls.append(self.name)
        return f"{self.name}:{secret}"


class APIFailingServiceProvider(ServiceProvider):
    calls: list[str] = []

    def get_secret(self, secret: str) -> str:
        self.calls.append(self.name)
        raise SecretRetrievalError("service failed")


class APITestCryptoProvider(CryptoProvider):
    def _key_file(self, key_file: str | Path | None) -> str:
        return str(key_file or self.settings.get("key_file", "default"))

    def encrypt(self, plaintext: str, key_file: str | Path | None = None) -> str:
        return f"{self.name}:{self._key_file(key_file)}:{plaintext}"

    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        return f"{self.name}:{self._key_file(key_file)}:{ciphertext}"

    def generate_key(self, output_path: str | Path | None = None) -> str:
        return str(output_path or self.settings.get("key_file", "provider-key"))


register_service_provider("api-test-echo", APIEchoServiceProvider)
register_service_provider("api-test-fail", APIFailingServiceProvider)
register_crypto_provider("api-test-crypto", APITestCryptoProvider)
register_service_provider("api-test-azure", AzureKeyVaultProvider)


class KeySecAPITests(unittest.TestCase):
    def test_public_facade_imports_remain_compatible(self) -> None:
        self.assertIs(KeySec, ModelKeySec)
        self.assertEqual(KeySec.__module__, "keysec.model.keysec")

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        config_path = Path(self.temp_dir.name) / "keysec.yaml"
        config_path.write_text(
            """
keysec:
  services:
    default: primary
    providers:
      primary:
        type: api-test-echo
      alternate:
        type: api-test-echo
      failing:
        type: api-test-fail
      backup:
        type: api-test-echo
  crypto:
    default: main
    providers:
      main:
        type: api-test-crypto
        settings:
          key_file: configured.key
      alternate:
        type: api-test-crypto
        settings:
          key_file: alternate.key
""",
            encoding="utf-8",
        )
        self.config_patch = patch.dict(
            "os.environ",
            {"KEYSEC_CONFIG": str(config_path)},
        )
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)
        self.keysec = KeySec()
        APIEchoServiceProvider.calls.clear()
        APIFailingServiceProvider.calls.clear()

    def test_get_secret_uses_default_and_named_provider(self) -> None:
        self.assertEqual(self.keysec.get_secret("db-password"), "primary:db-password")
        self.assertEqual(
            self.keysec.get_secret("db-password", provider="alternate"),
            "alternate:db-password",
        )

    def test_get_secret_rejects_unknown_provider(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "not configured"):
            self.keysec.get_secret("db-password", provider="missing")

    def test_provider_failure_does_not_fall_back(self) -> None:
        with self.assertRaisesRegex(SecretRetrievalError, "service failed"):
            self.keysec.get_secret("db-password", provider="failing")
        self.assertEqual(APIFailingServiceProvider.calls, ["failing"])
        self.assertEqual(APIEchoServiceProvider.calls, [])

    def test_get_secret_rejects_empty_or_non_string_name(self) -> None:
        with self.assertRaises(ValueError):
            self.keysec.get_secret("")
        with self.assertRaises(ValueError):
            self.keysec.get_secret(42)  # type: ignore[arg-type]

    def test_get_provider_returns_configured_service_or_crypto_instance(self) -> None:
        service = self.keysec.get_provider("primary")
        crypto = self.keysec.get_provider("main", provider_type="crypto")

        self.assertIsInstance(service, APIEchoServiceProvider)
        self.assertEqual(service.name, "primary")
        self.assertIsInstance(crypto, APITestCryptoProvider)
        self.assertEqual(crypto.name, "main")
        self.assertEqual(crypto.settings["key_file"], "configured.key")

    def test_get_provider_uses_type_to_resolve_duplicate_names(self) -> None:
        service = self.keysec.get_provider("alternate", provider_type="service")
        crypto = self.keysec.get_provider("alternate", provider_type="crypto")

        self.assertIsInstance(service, APIEchoServiceProvider)
        self.assertIsInstance(crypto, APITestCryptoProvider)

    def test_get_provider_rejects_ambiguous_name(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "ambiguous"):
            self.keysec.get_provider("alternate")

    def test_get_provider_rejects_unknown_name_or_type(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "not configured"):
            self.keysec.get_provider("missing")
        with self.assertRaisesRegex(ConfigurationError, "Provider type"):
            self.keysec.get_provider("primary", provider_type="unknown")

    def test_get_provider_rejects_missing_name_for_selected_type(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "Crypto provider.*not configured"):
            self.keysec.get_provider("primary", provider_type="crypto")

    def test_facade_does_not_expose_crypto_operations(self) -> None:
        self.assertFalse(hasattr(self.keysec, "encrypt"))
        self.assertFalse(hasattr(self.keysec, "decrypt"))
        self.assertFalse(hasattr(self.keysec, "generate_key"))

    def test_facade_returns_builtin_aes_gcm_provider(self) -> None:
        key_file = Path(self.temp_dir.name) / "facade.key"
        config_path = Path(self.temp_dir.name) / "aes.yaml"
        config_path.write_text(
            f"""
keysec:
  crypto:
    default: local
    providers:
      local:
        type: aes-gcm
        settings:
          key_file: {key_file}
""",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            keysec = KeySec()
            provider = keysec.get_provider("local", provider_type="crypto")
            generated_path = provider.generate_key()
            ciphertext = provider.encrypt("facade payload")

        self.assertEqual(generated_path, str(key_file))
        self.assertEqual(provider.decrypt(ciphertext), "facade payload")

    def test_facade_retrieves_from_azure_provider(self) -> None:
        config_path = Path(self.temp_dir.name) / "azure.yaml"
        config_path.write_text(
            """
keysec:
  services:
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
""",
            encoding="utf-8",
        )
        credential = MagicMock()
        client = MagicMock()
        client.get_secret.return_value = SimpleNamespace(value="integration-secret")

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            with patch(
                "keysec.providers.service.azure_key_vault.DefaultAzureCredential",
                return_value=credential,
            ):
                with patch(
                    "keysec.providers.service.azure_key_vault.SecretClient",
                    return_value=client,
                ):
                    keysec = KeySec()
                    result = keysec.get_secret("database-password")

        self.assertEqual(result, "integration-secret")
        client.get_secret.assert_called_once_with("database-password")
        client.close.assert_called_once()
        credential.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
