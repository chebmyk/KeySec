"""Models for the validated KeySec configuration."""

from dataclasses import dataclass, field

from keysec.model.provider_group_config import ProviderGroupConfig


@dataclass(frozen=True)
class AuditLoggingConfig:
    """Validated audit logging settings."""

    enabled: bool = False
    file: str = "./audit.log"


@dataclass(frozen=True)
class KeySecConfig:
    """Validated service and crypto provider configuration."""

    services: ProviderGroupConfig
    crypto: ProviderGroupConfig
    audit_logging: AuditLoggingConfig = field(default_factory=AuditLoggingConfig)
