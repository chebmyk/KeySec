"""Azure Key Vault service provider."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from azure.core.exceptions import AzureError, ResourceNotFoundError
from azure.identity import (
    CertificateCredential,
    ClientSecretCredential,
    DefaultAzureCredential,
)
from azure.keyvault.secrets import SecretClient

from keysec.model.errors import (
    ConfigurationError,
    SecretNotFoundError,
    SecretRetrievalError,
)
from keysec.model.provider_config import DecryptedConfigValue, EnvironmentConfigValue
from keysec.providers.service.service_provider import ServiceProvider


class AzureKeyVaultProvider(ServiceProvider):
    """Retrieves string secrets from Azure Key Vault."""

    def __init__(self, name: str, settings: Mapping[str, Any]) -> None:
        super().__init__(name, settings)
        vault_url = self.settings.get("vault_url")
        if not isinstance(vault_url, str) or not vault_url.startswith("https://"):
            raise ValueError(
                "Azure Key Vault provider requires an HTTPS 'vault_url' setting"
            )
        self._vault_url = vault_url
        self._service_principal = self._validate_service_principal(self.settings)

    def get_secret(self, secret: str) -> str:
        if not isinstance(secret, str) or not secret:
            raise ValueError("Secret name must be a non-empty string")

        credential = None
        client: SecretClient | None = None
        try:
            credential = self._create_credential()
            client = SecretClient(vault_url=self._vault_url, credential=credential)
            result = client.get_secret(secret)
            if result.value is None:
                raise SecretRetrievalError(
                    "Azure Key Vault returned a secret without a string value"
                )
            return result.value
        except ConfigurationError:
            raise
        except ResourceNotFoundError as exc:
            raise SecretNotFoundError(
                "The requested secret was not found in Azure Key Vault"
            ) from exc
        except AzureError as exc:
            raise SecretRetrievalError(
                "Azure Key Vault secret retrieval failed"
            ) from exc
        except ValueError as exc:
            raise SecretRetrievalError("Azure Key Vault authentication failed") from exc
        finally:
            if client is not None:
                client.close()
            if credential is not None:
                credential.close()

    @staticmethod
    def _validate_service_principal(
        settings: Mapping[str, Any],
    ) -> Mapping[str, str] | None:
        if "authentication" in settings:
            raise ConfigurationError(
                "Configure Azure service-principal settings directly in provider "
                "settings, not under 'authentication'"
            )
        if "password" in settings or "certificate_password" in settings:
            raise ConfigurationError(
                "Password-protected Azure Key Vault certificates are not supported"
            )

        tenant_id = settings.get("tenant_id")
        client_id = settings.get("client_id")
        client_secret = settings.get("client_secret")
        certificate_path = settings.get("certificate_path")
        if all(
            value is None
            for value in (tenant_id, client_id, client_secret, certificate_path)
        ):
            return None

        if not isinstance(tenant_id, str) or not tenant_id.strip():
            raise ConfigurationError(
                "Azure service-principal settings require a non-empty 'tenant_id'"
            )
        if not isinstance(client_id, str) or not client_id.strip():
            raise ConfigurationError(
                "Azure service-principal settings require a non-empty 'client_id'"
            )

        if certificate_path is not None:
            if not isinstance(certificate_path, str) or not certificate_path.strip():
                raise ConfigurationError(
                    "'certificate_path' must be a non-empty local file path"
                )
            path = Path(certificate_path).expanduser()
            try:
                if not path.is_file():
                    raise OSError
                with path.open("rb"):
                    pass
            except OSError as exc:
                raise ConfigurationError(
                    "Azure Key Vault certificate file is unavailable or unreadable"
                ) from exc
            return {
                "tenant_id": tenant_id,
                "client_id": client_id,
                "certificate_path": str(path),
            }

        if not isinstance(client_secret, str) or not client_secret.strip():
            raise ConfigurationError(
                "Azure service-principal settings require 'client_secret' "
                "(an environment variable name) or 'certificate_path'"
            )
        if not isinstance(
            client_secret, (DecryptedConfigValue, EnvironmentConfigValue)
        ) and not os.environ.get(client_secret):
            raise ConfigurationError(
                f"Azure Key Vault client-secret environment variable "
                f"'{client_secret}' is not set"
            )
        return {
            "tenant_id": tenant_id,
            "client_id": client_id,
            "client_secret": client_secret,
        }

    def _create_credential(
        self,
    ) -> DefaultAzureCredential | ClientSecretCredential | CertificateCredential:
        if self._service_principal is None:
            return DefaultAzureCredential()

        tenant_id = self._service_principal["tenant_id"]
        client_id = self._service_principal["client_id"]
        if "certificate_path" in self._service_principal:
            return CertificateCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                certificate_path=self._service_principal["certificate_path"],
            )

        if "client_secret" in self._service_principal:
            configured_secret = self._service_principal["client_secret"]
            if isinstance(
                configured_secret, (DecryptedConfigValue, EnvironmentConfigValue)
            ):
                client_secret = str(configured_secret)
            else:
                client_secret = os.environ.get(configured_secret)
            if not client_secret:
                raise ConfigurationError(
                    "Azure Key Vault client-secret value is unavailable"
                )
            return ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret,
            )

        raise ConfigurationError(
            "Azure service-principal settings have no usable credential source"
        )
