"""Registry for cryptography-provider implementations."""

from keysec.providers.crypto.crypto_provider import CryptoProvider
from keysec.providers.provider_registry import ProviderRegistry


class CryptoProviderRegistry(ProviderRegistry[CryptoProvider]):
    """Registry for cryptography-provider implementations."""

    def __init__(self) -> None:
        super().__init__(CryptoProvider)


crypto_provider_registry = CryptoProviderRegistry()


def register_crypto_provider(
    implementation_type: str,
    implementation: type[CryptoProvider],
) -> None:
    """Register an in-process crypto-provider implementation."""
    crypto_provider_registry.register(implementation_type, implementation)
