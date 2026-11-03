"""Shared base abstraction for configured providers."""

from abc import ABC
from types import MappingProxyType
from typing import Any, Mapping


class Provider(ABC):
    """Common identity and provider-owned settings for a configured provider."""

    def __init__(self, name: str, settings: Mapping[str, Any]) -> None:
        if not name:
            raise ValueError("Provider name must not be empty")
        self._name = name
        self._settings = MappingProxyType(dict(settings))

    @property
    def name(self) -> str:
        """Configured provider name."""
        return self._name

    @property
    def settings(self) -> Mapping[str, Any]:
        """Read-only provider-specific settings."""
        return self._settings
