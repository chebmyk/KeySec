"""Model for the validated KeySec configuration."""

from dataclasses import dataclass

from keysec.model.provider_group_config import ProviderGroupConfig


@dataclass(frozen=True)
class KeySecConfig:
    """Validated service and crypto provider configuration."""

    services: ProviderGroupConfig
    crypto: ProviderGroupConfig
