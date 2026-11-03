# Proposal

## Why

Ciphertext and secret identifiers are currently passed as bare strings, so callers cannot readily distinguish encrypted values from ordinary text or secret references from literal secret names. Consistent wrappers also let operators store encrypted provider-setting values in the main configuration and have KeySec decrypt them without putting plaintext credentials there.

## What Changes

- Add category-level cipher prefixes under `keysec.crypto.cipher_prefix` and `keysec.services.cipher_prefix`, defaulting to `ENC`, with per-provider `settings.cipher_prefix` overrides.
- Keep the service secret-reference prefix separate, defaulting to `KEY` and overridable per service provider with `secret_prefix`.
- **BREAKING**: Wrap encrypted output as `ENC(ciphertext)` and accept that wrapper when decrypting.
- Allow `get_secret` to accept `KEY(secret_id)` and resolve the enclosed identifier through the selected service provider.
- Decrypt matching wrapped string values in provider settings using the configured default crypto provider. For Azure Key Vault, an encrypted `client_secret` is passed directly as the credential; an unwrapped value retains its existing environment-variable-name behavior.
- Continue accepting existing unwrapped ciphertext and secret identifiers.
- Preserve the AES-GCM version marker inside the new outer wrapper.
- Keep prefix controls and the default crypto provider's bootstrap settings, including its key-file path, in plaintext so configuration decryption can be initialized.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cryptography`: Define configurable crypto-provider prefixes and wrapped encryption/decryption behavior.
- `secret-retrieval`: Define configurable service-provider prefixes and wrapped secret-reference behavior.

## Impact

Affected areas include YAML configuration loading and provider configuration, the crypto and service provider contracts, AES-GCM encryption/decryption, provider-setting resolution, Azure Key Vault credential handling, their tests, and the README configuration/API examples. No new dependency or public facade method is required.
