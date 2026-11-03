"""Abstract contract for read-only secret service providers."""

from abc import ABC, abstractmethod
from typing import Any, Mapping

from keysec.model.errors import ConfigurationError
from keysec.providers.provider import Provider


class ServiceProvider(Provider, ABC):
    """Provider contract for read-only secret retrieval."""

    def __init__(self, name: str, settings: Mapping[str, Any]) -> None:
        super().__init__(name, settings)
        secret_prefix = self.settings.get("secret_prefix", "KEY")
        if not isinstance(secret_prefix, str) or not secret_prefix:
            raise ConfigurationError(
                "Service provider 'secret_prefix' must be a non-empty string"
            )
        self._secret_prefix = secret_prefix

    @property
    def secret_prefix(self) -> str:
        """Configured prefix for wrapped secret references."""
        return self._secret_prefix

    @abstractmethod
    def get_secret(self, secret: str) -> str:
        """Return the named secret value."""
