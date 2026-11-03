"""Tests for Azure Key Vault service retrieval."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from azure.core.exceptions import AzureError, ClientAuthenticationError, ResourceNotFoundError

from keysec.model.errors import (
    ConfigurationError,
    SecretNotFoundError,
    SecretRetrievalError,
)
from keysec.model.provider_config import DecryptedConfigValue, EnvironmentConfigValue
from keysec.providers.service.azure_key_vault import AzureKeyVaultProvider


class AzureKeyVaultProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.provider = AzureKeyVaultProvider(
            "vault",
            {"vault_url": "https://example.vault.azure.net/"},
        )
        self.credential = MagicMock()
        self.client = MagicMock()
        self.credential_patch = patch(
            "keysec.providers.service.azure_key_vault.DefaultAzureCredential",
            return_value=self.credential,
        )
        self.client_patch = patch(
            "keysec.providers.service.azure_key_vault.SecretClient",
            return_value=self.client,
        )
        self.ambient_credential_factory = self.credential_patch.start()
        self.client_patch.start()
        self.addCleanup(self.credential_patch.stop)
        self.addCleanup(self.client_patch.stop)

    def test_returns_secret_value_as_string_and_closes_resources(self) -> None:
        self.client.get_secret.return_value = SimpleNamespace(value="secret-value")

        result = self.provider.get_secret("database-password")

        self.assertEqual(result, "secret-value")
        self.client.get_secret.assert_called_once_with("database-password")
        self.client.close.assert_called_once()
        self.credential.close.assert_called_once()

    def test_reports_missing_secret_without_exposing_provider_details(self) -> None:
        self.client.get_secret.side_effect = ResourceNotFoundError(
            "response included sensitive value"
        )

        with self.assertRaises(SecretNotFoundError) as raised:
            self.provider.get_secret("missing")

        self.assertNotIn("sensitive value", str(raised.exception))
        self.client.close.assert_called_once()
        self.credential.close.assert_called_once()

    def test_reports_authentication_failure_safely(self) -> None:
        self.client.get_secret.side_effect = ClientAuthenticationError(
            "credential detail"
        )

        with self.assertRaises(SecretRetrievalError) as raised:
            self.provider.get_secret("database-password")

        self.assertNotIn("credential detail", str(raised.exception))

    def test_reports_service_failure_safely(self) -> None:
        self.client.get_secret.side_effect = AzureError("service detail")

        with self.assertRaises(SecretRetrievalError) as raised:
            self.provider.get_secret("database-password")

        self.assertNotIn("service detail", str(raised.exception))

    def test_requires_https_vault_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            AzureKeyVaultProvider("bad", {"vault_url": "http://example.test"})

    def test_authenticates_service_principal_with_client_secret_environment_variable(
        self,
    ) -> None:
        settings = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "KEYSEC_TEST_CLIENT_SECRET",
        }
        self.client.get_secret.return_value = SimpleNamespace(value="secret-value")

        with patch.dict(os.environ, {"KEYSEC_TEST_CLIENT_SECRET": "private-value"}):
            provider = AzureKeyVaultProvider("vault", settings)
            with patch(
                "keysec.providers.service.azure_key_vault.ClientSecretCredential",
                return_value=self.credential,
            ) as credential_factory:
                self.assertEqual(provider.get_secret("database-password"), "secret-value")

        credential_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            client_secret="private-value",
        )
        self.client.close.assert_called_once()
        self.credential.close.assert_called_once()

    def test_authenticates_with_environment_expanded_client_secret(self) -> None:
        settings = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": EnvironmentConfigValue("private-value"),
        }
        self.client.get_secret.return_value = SimpleNamespace(value="secret-value")

        with patch.dict(os.environ, {}, clear=True):
            provider = AzureKeyVaultProvider("vault", settings)
            with patch(
                "keysec.providers.service.azure_key_vault.ClientSecretCredential",
                return_value=self.credential,
            ) as credential_factory:
                self.assertEqual(provider.get_secret("database-password"), "secret-value")

        credential_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            client_secret="private-value",
        )

    def test_authenticates_with_decrypted_client_secret_directly(self) -> None:
        settings = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": DecryptedConfigValue("private-value"),
        }
        self.client.get_secret.return_value = SimpleNamespace(value="secret-value")

        with patch.dict(os.environ, {}, clear=True):
            provider = AzureKeyVaultProvider("vault", settings)
            with patch(
                "keysec.providers.service.azure_key_vault.ClientSecretCredential",
                return_value=self.credential,
            ) as credential_factory:
                self.assertEqual(provider.get_secret("database-password"), "secret-value")

        credential_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            client_secret="private-value",
        )

    def test_authenticates_service_principal_with_local_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            certificate_path = Path(temp_dir) / "service-principal.pem"
            certificate_path.write_bytes(b"test certificate")
            settings = {
                "vault_url": "https://example.vault.azure.net/",
                "tenant_id": "tenant-id",
                "client_id": "client-id",
                "certificate_path": str(certificate_path),
            }
            self.client.get_secret.return_value = SimpleNamespace(value="secret-value")

            provider = AzureKeyVaultProvider("vault", settings)
            with patch(
                "keysec.providers.service.azure_key_vault.CertificateCredential",
                return_value=self.credential,
            ) as credential_factory:
                self.assertEqual(provider.get_secret("database-password"), "secret-value")

        credential_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            certificate_path=str(certificate_path),
        )
        self.credential.close.assert_called_once()

    def test_certificate_takes_precedence_without_reading_client_secret_variable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            certificate_path = Path(temp_dir) / "service-principal.pem"
            certificate_path.write_bytes(b"test certificate")
            settings = {
                "vault_url": "https://example.vault.azure.net/",
                "tenant_id": "tenant-id",
                "client_id": "client-id",
                "client_secret": "KEYSEC_MISSING_CLIENT_SECRET",
                "certificate_path": str(certificate_path),
            }
            self.client.get_secret.return_value = SimpleNamespace(value="secret-value")

            with patch.dict(os.environ, {}, clear=True):
                provider = AzureKeyVaultProvider("vault", settings)
                with patch(
                    "keysec.providers.service.azure_key_vault.CertificateCredential",
                    return_value=self.credential,
                ) as certificate_factory:
                    with patch(
                        "keysec.providers.service.azure_key_vault.ClientSecretCredential"
                    ) as secret_factory:
                        self.assertEqual(
                            provider.get_secret("database-password"), "secret-value"
                        )

        certificate_factory.assert_called_once_with(
            tenant_id="tenant-id",
            client_id="client-id",
            certificate_path=str(certificate_path),
        )
        secret_factory.assert_not_called()
        self.ambient_credential_factory.assert_not_called()

    def test_missing_client_secret_environment_variable_fails_without_fallback(
        self,
    ) -> None:
        settings = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "client_secret": "KEYSEC_MISSING_CLIENT_SECRET",
        }

        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "environment variable"):
                AzureKeyVaultProvider("vault", settings)

        self.ambient_credential_factory.assert_not_called()

    def test_rejects_incomplete_service_principal_settings(self) -> None:
        settings_without_client_id = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_secret": "KEYSEC_TEST_CLIENT_SECRET",
        }
        with patch.dict(os.environ, {"KEYSEC_TEST_CLIENT_SECRET": "private-value"}):
            with self.assertRaisesRegex(ConfigurationError, "client_id"):
                AzureKeyVaultProvider("vault", settings_without_client_id)

        settings_without_credential = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
        }
        with self.assertRaisesRegex(ConfigurationError, "client_secret"):
            AzureKeyVaultProvider("vault", settings_without_credential)

    def test_rejects_unavailable_certificate_file(self) -> None:
        settings = {
            "vault_url": "https://example.vault.azure.net/",
            "tenant_id": "tenant-id",
            "client_id": "client-id",
            "certificate_path": "/missing/service-principal.pem",
        }

        with self.assertRaisesRegex(ConfigurationError, "unavailable or unreadable"):
            AzureKeyVaultProvider("vault", settings)

    def test_rejects_unsupported_certificate_password_setting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            certificate_path = Path(temp_dir) / "service-principal.pem"
            certificate_path.write_bytes(b"test certificate")
            settings = {
                "vault_url": "https://example.vault.azure.net/",
                "tenant_id": "tenant-id",
                "client_id": "client-id",
                "certificate_path": str(certificate_path),
                "password": "must-not-be-configured",
            }

            with self.assertRaisesRegex(ConfigurationError, "Password-protected"):
                AzureKeyVaultProvider("vault", settings)

    def test_rejects_obsolete_nested_authentication_settings(self) -> None:
        settings = {
            "vault_url": "https://example.vault.azure.net/",
            "authentication": {
                "type": "service-principal",
                "tenant_id": "tenant-id",
                "client_id": "client-id",
                "client_secret_env": "KEYSEC_TEST_CLIENT_SECRET",
            },
        }

        with self.assertRaisesRegex(ConfigurationError, "directly in provider settings"):
            AzureKeyVaultProvider("vault", settings)


if __name__ == "__main__":
    unittest.main()
