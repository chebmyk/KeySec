"""Exceptions raised by KeySec configuration and provider operations."""


class KeySecError(Exception):
    """Base exception for KeySec operations."""


class ConfigurationError(ValueError):
    """Raised when KeySec configuration is missing or invalid."""


class SecretRetrievalError(KeySecError):
    """Raised when a configured service cannot retrieve a secret."""


class SecretNotFoundError(SecretRetrievalError):
    """Raised when the selected service does not contain the requested secret."""


class CryptoError(KeySecError):
    """Raised when a cryptographic operation fails."""
