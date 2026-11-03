"""Model for one named provider configuration."""

from dataclasses import dataclass
from typing import Any, Mapping


class DecryptedConfigValue(str):
    """String value decrypted from a wrapped provider setting."""


class EnvironmentConfigValue(str):
    """String value expanded from an environment variable."""


@dataclass(frozen=True)
class ProviderConfig:
    """One named provider configuration."""

    name: str
    type: str
    settings: Mapping[str, Any]
