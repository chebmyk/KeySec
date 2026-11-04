"""Public KeySec facade."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any, Callable

from keysec.config import load_config
from keysec.model.errors import ConfigurationError
from keysec.model.keysec_config import KeySecConfig
from keysec.model.provider_config import DecryptedConfigValue, ProviderConfig
from keysec.model.provider_group_config import ProviderGroupConfig
from keysec.providers.crypto.crypto_provider import CryptoProvider
from keysec.providers.crypto.crypto_provider_registry import crypto_provider_registry
from keysec.providers.provider import Provider
from keysec.providers.service.service_provider_registry import service_provider_registry


def _resolve_group_settings(
    group: ProviderGroupConfig,
    category: str,
    decrypt: Callable[[str], str],
    bootstrap_crypto_provider: str | None,
) -> ProviderGroupConfig:
    providers: dict[str, ProviderConfig] = {}
    for name, config in group.providers.items():
        if category == "crypto" and name == bootstrap_crypto_provider:
            providers[name] = config
            continue
        prefix = config.settings["cipher_prefix"]
        settings = _resolve_setting_value(config.settings, prefix, decrypt)
        providers[name] = ProviderConfig(
            name=config.name,
            type=config.type,
            settings=MappingProxyType(settings),
        )
    return ProviderGroupConfig(
        default=group.default,
        providers=MappingProxyType(providers),
        cipher_prefix=group.cipher_prefix,
    )


def _resolve_setting_value(
    value: Any,
    prefix: str,
    decrypt: Callable[[str], str],
    key: str = "",
) -> Any:
    if key in ("cipher_prefix", "secret_prefix"):
        return value
    if isinstance(value, Mapping):
        return {
            nested_key: _resolve_setting_value(
                nested_value,
                prefix,
                decrypt,
                nested_key if isinstance(nested_key, str) else "",
            )
            for nested_key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [_resolve_setting_value(item, prefix, decrypt) for item in value]
    if not isinstance(value, str) or not value.startswith(f"{prefix}("):
        return value
    if not value.endswith(")"):
        raise ConfigurationError("Wrapped provider setting is malformed")

    ciphertext = value[len(prefix) + 1:-1]
    if not ciphertext:
        raise ConfigurationError("Wrapped provider setting must not be empty")
    plaintext = decrypt(ciphertext)
    if not isinstance(plaintext, str):
        raise ConfigurationError("Crypto provider returned a non-string setting value")
    return DecryptedConfigValue(plaintext)


class KeySec:
    """Public facade for secret retrieval and configured provider lookup."""

    def __init__(self) -> None:
        config = load_config()
        decryptor: CryptoProvider | None = None

        def decrypt(ciphertext: str) -> str:
            nonlocal decryptor
            if decryptor is None:
                crypto_config = config.crypto.select(None)
                decryptor = crypto_provider_registry.create(crypto_config)
            return decryptor.decrypt(ciphertext)

        self._config = KeySecConfig(
            services=_resolve_group_settings(
                config.services,
                "services",
                decrypt,
                config.crypto.default,
            ),
            crypto=_resolve_group_settings(
                config.crypto,
                "crypto",
                decrypt,
                config.crypto.default,
            ),
        )

    def get_secret(self, secret: str, provider: str | None = None) -> str:
        """Retrieve a secret value as a string."""
        if not isinstance(secret, str) or not secret:
            raise ValueError("Secret name must be a non-empty string")
        selected = self._config.services.select(provider)
        service = service_provider_registry.create(selected)
        prefix = f"{service.secret_prefix}("
        if secret.startswith(prefix) and secret.endswith(")"):
            secret = secret[len(prefix):-1]
            if not secret:
                raise ValueError("Secret name inside wrapper must be non-empty")
        return service.get_secret(secret)

    def get_provider(
        self,
        name: str | None = None,
        provider_type: str | None = None,
    ) -> Provider:
        """Return the configured provider instance selected by name."""
        if name is not None and (not isinstance(name, str) or not name):
            raise ValueError("Provider name must be a non-empty string")
        if provider_type not in (None, "service", "crypto"):
            raise ConfigurationError("Provider type must be 'service' or 'crypto'")

        if provider_type == "service":
            if name is None:
                return service_provider_registry.create(
                    self._config.services.select(None)
                )
            service_config = self._config.services.providers.get(name)
            if service_config is None:
                raise ConfigurationError(f"Service provider '{name}' is not configured")
            return service_provider_registry.create(service_config)
        if provider_type == "crypto":
            if name is None:
                return crypto_provider_registry.create(
                    self._config.crypto.select(None)
                )
            crypto_config = self._config.crypto.providers.get(name)
            if crypto_config is None:
                raise ConfigurationError(f"Crypto provider '{name}' is not configured")
            return crypto_provider_registry.create(crypto_config)
        if name is None:
            raise ConfigurationError(
                "Provider type must be specified when selecting a default provider"
            )

        service_config = self._config.services.providers.get(name)
        crypto_config = self._config.crypto.providers.get(name)

        if service_config is not None and crypto_config is not None:
            raise ConfigurationError(
                f"Provider name '{name}' is ambiguous; specify provider_type"
            )
        if service_config is not None:
            return service_provider_registry.create(service_config)
        if crypto_config is not None:
            return crypto_provider_registry.create(crypto_config)
        raise ConfigurationError(f"Provider '{name}' is not configured")
