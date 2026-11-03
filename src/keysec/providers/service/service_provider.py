"""Abstract contract for read-only secret service providers."""

from abc import ABC, abstractmethod

from keysec.providers.provider import Provider


class ServiceProvider(Provider, ABC):
    """Provider contract for read-only secret retrieval."""

    @abstractmethod
    def get_secret(self, secret: str) -> str:
        """Return the named secret value."""
