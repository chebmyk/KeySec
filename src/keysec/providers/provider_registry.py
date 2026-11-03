"""Generic registry for provider implementation classes."""

from typing import Generic, TypeVar

from keysec.model.errors import ConfigurationError
from keysec.model.provider_config import ProviderConfig
from keysec.providers.provider import Provider

ProviderType = TypeVar("ProviderType", bound=Provider)


class ProviderRegistry(Generic[ProviderType]):
    """Maps configured implementation types to provider classes."""

    def __init__(self, base_class: type[ProviderType]) -> None:
        self._base_class = base_class
        self._implementations: dict[str, type[ProviderType]] = {}

    def register(
        self,
        implementation_type: str,
        implementation: type[ProviderType],
    ) -> None:
        if not implementation_type:
            raise ValueError("Provider implementation type must not be empty")
        if not issubclass(implementation, self._base_class):
            raise TypeError(
                f"Provider implementation must derive from {self._base_class.__name__}"
            )
        if implementation_type in self._implementations:
            raise ValueError(
                f"Provider implementation type '{implementation_type}' is already registered"
            )
        self._implementations[implementation_type] = implementation

    def create(self, config: ProviderConfig) -> ProviderType:
        try:
            implementation = self._implementations[config.type]
        except KeyError as exc:
            raise ConfigurationError(
                f"Provider implementation type '{config.type}' is not registered"
            ) from exc
        return implementation(config.name, config.settings)
