# Design

## Context

Provider settings already flow from YAML through `ProviderConfig` and the registries into provider instances. AES-GCM returns provider-specific cipher prefixes currently live only in provider settings. See the proposal and capability deltas for the requested behavior.

## Goals / Non-Goals

**Goals:**
- Keep each prefix override with its named provider configuration.
- Apply consistent wrapper semantics while retaining support for existing raw inputs.
- Preserve the AES-GCM payload and versioning inside the new outer wrapper.
- Resolve encrypted values in provider settings using the configured default crypto provider, including service credentials.

**Non-Goals:**
- Change provider selection, cryptographic algorithms, ciphertext payload contents, or secret-service behavior.
- Add crypto operations to the `KeySec` facade.

## Decisions

- Store category defaults at `keysec.crypto.cipher_prefix` and `keysec.services.cipher_prefix`, both defaulting to `ENC`. A provider's `settings.cipher_prefix` overrides its category value. Preserve `secret_prefix` as a separate service-provider setting defaulting to `KEY` for `get_secret` references.
- Validate category and provider prefixes as non-empty strings and report invalid configuration explicitly. Do not silently coerce other YAML values.
- Treat crypto wrapping as part of the `CryptoProvider` operation contract. Built-in and custom implementations use the configured prefix for `encrypt` output and remove that exact wrapper before decrypting. Keep the existing wrapped payload available for legacy-input compatibility rather than moving prefix parsing into `KeySec.get_provider`, which returns providers for direct use.
- Before constructing a configured provider, recursively inspect its setting values. When a string has the effective category/provider `cipher_prefix` wrapper, remove that wrapper and decrypt its payload with the configured default crypto provider. Leave unwrapped values unchanged. Prefix controls and the default crypto provider's bootstrap settings (including its configured key-file path) remain plaintext so the resolver can initialize.
- For a wrapped setting value, use the target category/provider prefix for wrapper recognition, then pass the unwrapped payload to the default crypto provider's `decrypt` operation. This permits service-specific prefix overrides while centralizing decryption in the default crypto provider.
- Resolve `get_secret` references after selecting the service provider, using its `secret_prefix` (or `KEY`) before forwarding the identifier. Keep unwrapped identifiers unchanged. This behavior is separate from decrypting provider settings.
- Interpret an Azure `client_secret` matching its effective cipher wrapper as an encrypted literal and pass the decrypted value directly to authentication. Preserve environment-variable lookup for unwrapped `client_secret` values. If a wrapped value fails to decrypt, surface the error; never retry it as an environment-variable name or use ambient identity.
- The default crypto provider and its key file must be configured separately from encrypted provider values. Encrypted values are not used to bootstrap that provider.
- Update README examples and provider-extension guidance so custom implementations follow the crypto wrapper contract and service wrapper configuration is clear.

## Risks / Trade-offs

- [Provider extension consistency] Custom crypto providers can return their own formats. The contract and extension documentation must make prefix wrapping explicit, and tests should cover a custom implementation as well as AES-GCM.
- [Prefix mismatch] A wrapper created with another provider's override cannot be decrypted or resolved by the selected provider. Keep selection explicit and surface the provider's existing format or retrieval error rather than trying other providers.
- [Accidental setting interpretation] A literal setting that starts with its effective `cipher_prefix` wrapper is treated as ciphertext. Document the reserved wrapper form and require operators to encrypt values intentionally before using it.
- [Bootstrap dependency] The default crypto provider cannot decrypt its own bootstrap settings. Keep its configuration and key-file path plaintext and provision the key file separately.

## Migration Plan

No stored data migration is required. New crypto output uses `ENC(...)` by default. Existing unwrapped secret identifiers and unwrapped environment-variable names continue to pass through unchanged. Operators may place encrypted provider-setting values in the YAML after configuring the default crypto provider and separately provisioned key file. Callers that exchange newly encrypted values with older KeySec versions must update those consumers or unwrap the outer prefix before sending the value; rolling back alone does not make newly wrapped output readable by older versions.
