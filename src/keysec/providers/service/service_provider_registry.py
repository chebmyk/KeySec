"""Registry for service-provider implementations."""

from keysec.providers.provider_registry import ProviderRegistry
from keysec.providers.service.service_provider import ServiceProvider


class ServiceProviderRegistry(ProviderRegistry[ServiceProvider]):
    """Registry for service-provider implementations."""

    def __init__(self) -> None:
        super().__init__(ServiceProvider)


service_provider_registry = ServiceProviderRegistry()


def register_service_provider(
    implementation_type: str,
    implementation: type[ServiceProvider],
) -> None:
    """Register an in-process service-provider implementation."""
    service_provider_registry.register(implementation_type, implementation)
