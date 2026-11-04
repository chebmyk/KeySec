"""Tests for the public KeySec facade."""

from __future__ import annotations

import inspect
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from keysec import KeySec
from keysec.model import KeySec as ModelKeySec
from keysec.model.errors import ConfigurationError, CryptoError, SecretRetrievalError
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
        ciphertext = f"{self.name}:{self._key_file(key_file)}:{plaintext}"
        return self.wrap_ciphertext(ciphertext)

    def decrypt(self, ciphertext: str, key_file: str | Path | None = None) -> str:
        ciphertext = self.unwrap_ciphertext(ciphertext)
        prefix = f"{self.name}:{self._key_file(key_file)}:"
        return ciphertext.removeprefix(prefix)

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
        settings:
          secret_prefix: ALT
      failing:
        type: api-test-fail
      backup:
        type: api-test-echo
      invalidprefix:
        type: api-test-echo
        settings:
          secret_prefix: 12
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
          cipher_prefix: LOCKED
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
        self.assertEqual(self.keysec.get_secret("KEY(db-password)"), "primary:db-password")
        self.assertEqual(
            self.keysec.get_secret("db-password", provider="alternate"),
            "alternate:db-password",
        )
        self.assertEqual(
            self.keysec.get_secret("ALT(db-password)", provider="alternate"),
            "alternate:db-password",
        )

    def test_get_secret_rejects_invalid_prefix_configuration(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "secret_prefix"):
            self.keysec.get_secret("KEY(db-password)", provider="invalidprefix")

    def test_get_secret_rejects_empty_wrapped_secret_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "inside wrapper"):
            self.keysec.get_secret("KEY()")

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

    def test_selected_providers_use_their_configured_prefixes(self) -> None:
        secret = self.keysec.get_secret("ALT(database-password)", provider="alternate")
        crypto = self.keysec.get_provider("alternate", provider_type="crypto")
        ciphertext = crypto.encrypt("integration payload")

        self.assertEqual(secret, "alternate:database-password")
        self.assertEqual(crypto.cipher_prefix, "LOCKED")
        self.assertTrue(ciphertext.startswith("LOCKED("))
        self.assertEqual(crypto.decrypt(ciphertext), "integration payload")

    def test_resolves_wrapped_crypto_and_service_provider_settings(self) -> None:
        bootstrap_crypto = APITestCryptoProvider(
            "main",
            {"key_file": "bootstrap.key", "cipher_prefix": "CRYPTO"},
        )
        crypto_ciphertext = bootstrap_crypto.encrypt("crypto-setting")
        crypto_value = (
            "SECONDARY("
            + bootstrap_crypto.unwrap_ciphertext(crypto_ciphertext)
            + ")"
        )
        service_value = "VAULT(main:bootstrap.key:service-setting)"
        nested_value = "VAULT(main:bootstrap.key:nested-setting)"
        config_path = Path(self.temp_dir.name) / "encrypted-settings.yaml"
        config_path.write_text(
            f"""
keysec:
  services:
    default: vault
    cipher_prefix: SERVICE
    providers:
      vault:
        type: api-test-echo
        settings:
          cipher_prefix: VAULT
          endpoint_token: {service_value}
          labels:
            - {nested_value}
            - plain-label
  crypto:
    default: main
    cipher_prefix: CRYPTO
    providers:
      main:
        type: api-test-crypto
        settings:
          key_file: bootstrap.key
      secondary:
        type: api-test-crypto
        settings:
          cipher_prefix: SECONDARY
          key_file: {crypto_value}
          unwrapped: unchanged
""",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            keysec = KeySec()
            service = keysec.get_provider("vault", provider_type="service")
            crypto = keysec.get_provider("secondary", provider_type="crypto")
            bootstrap = keysec.get_provider("main", provider_type="crypto")

        self.assertEqual(service.settings["endpoint_token"], "service-setting")
        self.assertEqual(service.settings["labels"], ["nested-setting", "plain-label"])
        self.assertEqual(crypto.settings["key_file"], "crypto-setting")
        self.assertEqual(crypto.settings["unwrapped"], "unchanged")
        self.assertEqual(bootstrap.settings["key_file"], "bootstrap.key")

    def test_wrapped_provider_setting_requires_default_crypto_provider(self) -> None:
        config_path = Path(self.temp_dir.name) / "no-default-crypto.yaml"
        config_path.write_text(
            """
keysec:
  services:
    providers:
      vault:
        type: api-test-echo
        settings:
          token: ENC(ciphertext)
  crypto:
    providers:
      local:
        type: api-test-crypto
""",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            with self.assertRaisesRegex(ConfigurationError, "no default"):
                KeySec()

    def test_malformed_wrapped_provider_setting_fails_explicitly(self) -> None:
        config_path = Path(self.temp_dir.name) / "malformed-encrypted-settings.yaml"
        config_path.write_text(
            """
keysec:
  services:
    providers:
      vault:
        type: api-test-echo
        settings:
          token: ENC(ciphertext
  crypto:
    default: main
    providers:
      main:
        type: api-test-crypto
""",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            with self.assertRaisesRegex(ConfigurationError, "malformed"):
                KeySec()

    def test_invalid_wrapped_ciphertext_fails_without_fallback(self) -> None:
        key_file = Path(self.temp_dir.name) / "bootstrap.key"
        key_file.write_bytes(bytes(range(32)))
        config_path = Path(self.temp_dir.name) / "invalid-ciphertext.yaml"
        config_path.write_text(
            f"""
keysec:
  services:
    providers:
      vault:
        type: api-test-echo
        settings:
          token: ENC(AAFEFEWRWR)
  crypto:
    default: main
    providers:
      main:
        type: aes-gcm
        settings:
          key_file: {key_file}
""",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            with self.assertRaises(CryptoError):
                KeySec()

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

    def test_facade_uses_decrypted_azure_client_secret_directly(self) -> None:
        bootstrap_crypto = APITestCryptoProvider(
            "main",
            {"key_file": "bootstrap.key", "cipher_prefix": "ENC"},
        )
        encrypted_secret = bootstrap_crypto.encrypt("private-client-secret")
        config_path = Path(self.temp_dir.name) / "encrypted-azure.yaml"
        config_path.write_text(
            f"""
keysec:
  services:
    default: vault
    cipher_prefix: ENC
    providers:
      vault:
        type: api-test-azure
        settings:
          vault_url: https://example.vault.azure.net/
          tenant_id: tenant-id
          client_id: client-id
          client_secret: {encrypted_secret}
  crypto:
    default: main
    providers:
      main:
        type: api-test-crypto
        settings:
          key_file: bootstrap.key
""",
            encoding="utf-8",
        )
        credential = MagicMock()
        client = MagicMock()
        client.get_secret.return_value = SimpleNamespace(value="integration-secret")

        with patch.dict(
            "os.environ",
            {
                "KEYSEC_CONFIG": str(config_path),
                "main:bootstrap.key:private-client-secret": "must-not-be-used",
            },
        ):
            with patch(
                "keysec.providers.service.azure_key_vault.ClientSecretCredential",
                return_value=credential,
            ) as credential_factory:
                with patch(
                    "keysec.providers.service.azure_key_vault.SecretClient",
                    return_value=client,
                ):
                    keysec = KeySec()
                    result = keysec.get_secret("KEY(database-password)")

        self.assertEqual(result, "integration-secret")
        credential_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            client_secret="private-client-secret",
        )
        client.get_secret.assert_called_once_with("database-password")

    def test_facade_uses_environment_expanded_azure_client_secret_directly(self) -> None:
        config_path = Path(self.temp_dir.name) / "expanded-azure.yaml"
        config_path.write_text(
            """
keysec:
  services:
    default: vault
    providers:
      vault:
        type: api-test-azure
        settings:
          vault_url: https://example.vault.azure.net/
          tenant_id: tenant-id
          client_id: client-id
          client_secret: ${SEC_VAR}
""",
            encoding="utf-8",
        )
        credential = MagicMock()
        client = MagicMock()
        client.get_secret.return_value = SimpleNamespace(value="integration-secret")

        with patch.dict(
            "os.environ",
            {
                "KEYSEC_CONFIG": str(config_path),
                "SEC_VAR": "private-client-secret",
            },
            clear=True,
        ):
            keysec = KeySec()
            with patch.dict(
                "os.environ",
                {"KEYSEC_CONFIG": str(config_path)},
                clear=True,
            ):
                with patch(
                    "keysec.providers.service.azure_key_vault.ClientSecretCredential",
                    return_value=credential,
                ) as credential_factory:
                    with patch(
                        "keysec.providers.service.azure_key_vault.SecretClient",
                        return_value=client,
                    ):
                        result = keysec.get_secret("database-password")

        self.assertEqual(result, "integration-secret")
        credential_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            client_secret="private-client-secret",
        )
        client.get_secret.assert_called_once_with("database-password")

    def test_audit_logging_records_supported_operations_without_payloads(self) -> None:
        audit_path = Path(self.temp_dir.name) / "audit.log"
        config_path = Path(self.temp_dir.name) / "audit-enabled.yaml"
        config_path.write_text(
            f"""
keysec:
  audit_logging:
    enabled: true
    file: {audit_path}
  services:
    default: primary
    providers:
      primary:
        type: api-test-echo
      failing:
        type: api-test-fail
  crypto:
    default: main
    providers:
      main:
        type: api-test-crypto
        settings:
          key_file: configured.key
""",
            encoding="utf-8",
        )

        with patch.dict("os.environ", {"KEYSEC_CONFIG": str(config_path)}):
            keysec = KeySec()
            self.assertIsNotNone(keysec._audit_logger)
            assert keysec._audit_logger is not None
            self.addCleanup(keysec._audit_logger.close)

            secret_name = "AUDIT_SECRET_NAME_MARKER"
            secret_value = keysec.get_secret(secret_name)
            crypto = keysec.get_provider("main", provider_type="crypto")
            self.assertIsInstance(crypto, APITestCryptoProvider)
            self.assertEqual(
                inspect.signature(crypto.encrypt),
                inspect.signature(
                    APITestCryptoProvider.encrypt.__get__(crypto, type(crypto))
                ),
            )
            plaintext = "AUDIT_PLAINTEXT_MARKER"
            ciphertext = crypto.encrypt(plaintext)
            self.assertEqual(crypto.decrypt(ciphertext), plaintext)
            crypto.generate_key()

            with self.assertRaisesRegex(SecretRetrievalError, "service failed"):
                keysec.get_secret(
                    "AUDIT_FAILED_SECRET_NAME_MARKER",
                    provider="failing",
                )

        contents = audit_path.read_text(encoding="utf-8")
        for sensitive_value in (
            secret_name,
            secret_value,
            "AUDIT_FAILED_SECRET_NAME_MARKER",
            plaintext,
            ciphertext,
            "service failed",
        ):
            self.assertNotIn(sensitive_value, contents)

        entries = [json.loads(line) for line in contents.splitlines()]
        self.assertEqual(
            [(entry["operation"], entry["outcome"]) for entry in entries],
            [
                ("secret_retrieval", "success"),
                ("encrypt", "success"),
                ("decrypt", "success"),
                ("key_generation", "success"),
                ("secret_retrieval", "failure"),
            ],
        )
        self.assertEqual(
            [entry["provider"] for entry in entries],
            ["primary", "main", "main", "main", "failing"],
        )


if __name__ == "__main__":
    unittest.main()
