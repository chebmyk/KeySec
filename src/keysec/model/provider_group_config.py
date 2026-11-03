"""Model for named providers and their optional default."""

from dataclasses import dataclass
from typing import Mapping

from keysec.model.errors import ConfigurationError
from keysec.model.provider_config import ProviderConfig


@dataclass(frozen=True)
class ProviderGroupConfig:
    """Named providers and an optional default for one provider category."""

    default: str | None
    providers: Mapping[str, ProviderConfig]

    def select(self, name: str | None) -> ProviderConfig:
        selected_name = name if name is not None else self.default
        if selected_name is None:
            raise ConfigurationError("No provider was selected and no default is configured")
        try:
            return self.providers[selected_name]
        except KeyError as exc:
            raise ConfigurationError(
                f"Provider '{selected_name}' is not configured"
            ) from exc
