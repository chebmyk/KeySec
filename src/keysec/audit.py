"""Privacy-preserving audit logging for KeySec operations."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from functools import wraps
import inspect
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Literal, ParamSpec, TypeVar

from keysec.model.keysec_config import AuditLoggingConfig

AuditOperation = Literal[
    "secret_retrieval",
    "encrypt",
    "decrypt",
    "key_generation",
]

P = ParamSpec("P")
R = TypeVar("R")
AuditProviderResolver = Callable[..., str | None]


def audit(
    operation: AuditOperation,
    provider_resolver: AuditProviderResolver | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Audit an instance method using its configured logger context."""

    def decorate(method: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(method)

        @wraps(method)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            instance = args[0] if args else None
            audit_logger = getattr(instance, "_audit_logger", None)
            if audit_logger is None:
                return method(*args, **kwargs)

            if provider_resolver is None:
                provider = getattr(instance, "name", None)
            else:
                provider = provider_resolver(signature, *args, **kwargs)

            return audit_logger.run(operation, provider, method, *args, **kwargs)

        setattr(wrapped, "__audit_operation__", operation)
        return wrapped

    return decorate


def _report_write_failure() -> None:
    try:
        logging.getLogger("keysec.audit.errors").error("Audit log write failed")
    except Exception:
        return


class _AuditFileHandler(TimedRotatingFileHandler):
    def handleError(self, record: logging.LogRecord) -> None:
        _report_write_failure()


class AuditLogger:
    """Write operation metadata to a dedicated daily-rotating log."""

    def __init__(self, file_path: str | Path) -> None:
        self._logger = logging.Logger("keysec.audit", level=logging.INFO)
        self._logger.propagate = False
        handler = _AuditFileHandler(
            file_path,
            when="midnight",
            interval=1,
            backupCount=0,
            encoding="utf-8",
            delay=True,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.addHandler(handler)

    def record(
        self,
        operation: AuditOperation,
        provider: str | None,
        succeeded: bool,
    ) -> None:
        try:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "operation": operation,
                "provider": provider,
                "outcome": "success" if succeeded else "failure",
            }
            self._logger.info(json.dumps(entry, separators=(",", ":")))
        except Exception:
            _report_write_failure()

    def run(
        self,
        operation: AuditOperation,
        provider_name: str | None,
        action: Callable[P, R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> R:
        try:
            result = action(*args, **kwargs)
        except Exception:
            self.record(operation, provider_name, succeeded=False)
            raise
        self.record(operation, provider_name, succeeded=True)
        return result

    def close(self) -> None:
        """Close the audit file handler."""
        for handler in self._logger.handlers:
            try:
                handler.close()
            except Exception:
                _report_write_failure()


def create_audit_logger(config: AuditLoggingConfig) -> AuditLogger | None:
    """Create an audit logger only when audit logging is enabled."""
    if not config.enabled:
        return None
    return AuditLogger(config.file)
