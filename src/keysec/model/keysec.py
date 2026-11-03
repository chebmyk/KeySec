"""Public KeySec facade."""

from __future__ import annotations

from keysec.config import load_config
from keysec.model.errors import ConfigurationError
from keysec.providers.crypto.crypto_provider_registry import crypto_provider_registry
from keysec.providers.provider import Provider
from keysec.providers.service.service_provider_registry import service_provider_registry


class KeySec:
    """Public facade for secret retrieval and configured provider lookup."""

    def __init__(self) -> None:
        self._config = load_config()

    def get_secret(self, secret: str, provider: str | None = None) -> str:
        """Retrieve a secret value as a string."""
        if not isinstance(secret, str) or not secret:
            raise ValueError("Secret name must be a non-empty string")
        selected = self._config.services.select(provider)
        service = service_provider_registry.create(selected)
        return service.get_secret(secret)

    def get_provider(
        self,
        name: str,
        provider_type: str | None = None,
    ) -> Provider:
        """Return the configured provider instance selected by name."""
        if not isinstance(name, str) or not name:
            raise ValueError("Provider name must be a non-empty string")
        if provider_type not in (None, "service", "crypto"):
            raise ConfigurationError("Provider type must be 'service' or 'crypto'")

        service_config = self._config.services.providers.get(name)
        crypto_config = self._config.crypto.providers.get(name)
        if provider_type == "service":
            if service_config is None:
                raise ConfigurationError(f"Service provider '{name}' is not configured")
            return service_provider_registry.create(service_config)
        if provider_type == "crypto":
            if crypto_config is None:
                raise ConfigurationError(f"Crypto provider '{name}' is not configured")
            return crypto_provider_registry.create(crypto_config)

        if service_config is not None and crypto_config is not None:
            raise ConfigurationError(
                f"Provider name '{name}' is ambiguous; specify provider_type"
            )
        if service_config is not None:
            return service_provider_registry.create(service_config)
        if crypto_config is not None:
            return crypto_provider_registry.create(crypto_config)
        raise ConfigurationError(f"Provider '{name}' is not configured")
