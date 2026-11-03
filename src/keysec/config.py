"""Configuration loading and validation for KeySec."""

from __future__ import annotations

import os
from pathlib import Path
import re
from types import MappingProxyType
from typing import Any

import yaml

from keysec.model.errors import ConfigurationError
from keysec.model.keysec_config import KeySecConfig
from keysec.model.provider_config import EnvironmentConfigValue, ProviderConfig
from keysec.model.provider_group_config import ProviderGroupConfig

_ENVIRONMENT_VARIABLE_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def load_config(path: str | Path | None = None) -> KeySecConfig:
    """Load configuration from an explicit path, KEYSEC_CONFIG, or ./keysec.yaml."""
    config_path = _config_path(path)
    try:
        raw_config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationError(
            f"Configuration file does not exist: {config_path}"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(
            f"Could not read configuration file: {config_path}"
        ) from exc
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Configuration file is not valid YAML: {config_path}"
        ) from exc

    raw_config = _expand_environment_values(raw_config)
    if not isinstance(raw_config, dict):
        raise ConfigurationError("Configuration document must be a YAML mapping")
    keysec_config = raw_config.get("keysec")
    if not isinstance(keysec_config, dict):
        raise ConfigurationError("'keysec' must be a YAML mapping")

    return KeySecConfig(
        services=_parse_group(keysec_config.get("services", {}), "keysec.services"),
        crypto=_parse_group(keysec_config.get("crypto", {}), "keysec.crypto"),
    )


def _expand_environment_values(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _expand_environment_values(nested_value)
            for key, nested_value in value.items()
        }
    if isinstance(value, list):
        return [_expand_environment_values(item) for item in value]
    if not isinstance(value, str) or not _ENVIRONMENT_VARIABLE_PATTERN.search(value):
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group(1)
        try:
            return os.environ[name]
        except KeyError as exc:
            raise ConfigurationError(
                f"Configuration references unset environment variable '{name}'"
            ) from exc

    return EnvironmentConfigValue(_ENVIRONMENT_VARIABLE_PATTERN.sub(replace, value))


def _config_path(path: str | Path | None) -> Path:
    if path is not None:
        return Path(path).expanduser()

    configured_path = os.environ.get("KEYSEC_CONFIG")
    if configured_path is not None:
        if not configured_path.strip():
            raise ConfigurationError("KEYSEC_CONFIG must not be empty")
        return Path(configured_path).expanduser()

    return Path.cwd() / "keysec.yaml"


def _parse_group(raw_group: Any, category: str) -> ProviderGroupConfig:
    if not isinstance(raw_group, dict):
        raise ConfigurationError(f"'{category}' must be a YAML mapping")

    cipher_prefix = raw_group.get("cipher_prefix", "ENC")
    if not isinstance(cipher_prefix, str) or not cipher_prefix:
        raise ConfigurationError(
            f"'{category}.cipher_prefix' must be a non-empty string"
        )

    default = raw_group.get("default")
    if default is not None and (not isinstance(default, str) or not default.strip()):
        raise ConfigurationError(f"'{category}.default' must be a non-empty provider name")

    raw_providers = raw_group.get("providers", {})
    if not isinstance(raw_providers, dict):
        raise ConfigurationError(f"'{category}.providers' must be a YAML mapping")

    providers: dict[str, ProviderConfig] = {}
    for name, raw_provider in raw_providers.items():
        if not isinstance(name, str) or not name.strip():
            raise ConfigurationError(
                f"'{category}.providers' keys must be non-empty provider names"
            )
        if not isinstance(raw_provider, dict):
            raise ConfigurationError(
                f"Configuration for {category} provider '{name}' must be a mapping"
            )

        provider_type = raw_provider.get("type")
        if not isinstance(provider_type, str) or not provider_type.strip():
            raise ConfigurationError(
                f"'{category}.providers.{name}.type' must be a non-empty string"
            )

        settings = raw_provider.get("settings", {})
        if not isinstance(settings, dict):
            raise ConfigurationError(
                f"'{category}.providers.{name}.settings' must be a YAML mapping"
            )
        if any(not isinstance(key, str) for key in settings):
            raise ConfigurationError(
                f"'{category}.providers.{name}.settings' keys must be strings"
            )
        provider_cipher_prefix = settings.get("cipher_prefix", cipher_prefix)
        if not isinstance(provider_cipher_prefix, str) or not provider_cipher_prefix:
            raise ConfigurationError(
                f"'{category}.providers.{name}.settings.cipher_prefix' "
                "must be a non-empty string"
            )
        resolved_settings = dict(settings)
        resolved_settings["cipher_prefix"] = provider_cipher_prefix

        providers[name] = ProviderConfig(
            name=name,
            type=provider_type,
            settings=MappingProxyType(resolved_settings),
        )

    if default is not None and default not in providers:
        raise ConfigurationError(
            f"'{category}.default' refers to an unconfigured provider '{default}'"
        )

    return ProviderGroupConfig(
        default=default,
        providers=MappingProxyType(providers),
        cipher_prefix=cipher_prefix,
    )
