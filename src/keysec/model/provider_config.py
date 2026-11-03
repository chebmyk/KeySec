"""Model for one named provider configuration."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProviderConfig:
    """One named provider configuration."""

    name: str
    type: str
    settings: Mapping[str, Any]
