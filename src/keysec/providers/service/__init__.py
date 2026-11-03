"""Service-provider contracts, registry, and implementations."""

from keysec.providers.service.azure_key_vault import AzureKeyVaultProvider
from keysec.providers.service.service_provider import ServiceProvider
from keysec.providers.service.service_provider_registry import (
    ServiceProviderRegistry,
    register_service_provider,
    service_provider_registry,
)

__all__ = [
    "AzureKeyVaultProvider",
    "ServiceProvider",
    "ServiceProviderRegistry",
    "register_service_provider",
    "service_provider_registry",
]
