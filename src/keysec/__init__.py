"""Secret retrieval and cryptography for Python applications."""

from keysec.model.keysec import KeySec
from keysec.providers.crypto.aes_gcm import AESGCMProvider
from keysec.providers.crypto.crypto_provider_registry import register_crypto_provider
from keysec.providers.service.azure_key_vault import AzureKeyVaultProvider
from keysec.providers.service.service_provider_registry import register_service_provider

register_service_provider("azure-key-vault", AzureKeyVaultProvider)
register_crypto_provider("aes-gcm", AESGCMProvider)

__version__ = "0.1.0"

__all__ = ["KeySec", "__version__"]
