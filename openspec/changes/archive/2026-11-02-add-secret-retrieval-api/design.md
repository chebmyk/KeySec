# Design

## Context

The repository is a greenfield scaffold with no Python package metadata, implementation, tests, or configuration conventions. See proposal.md for motivation and the capability specs for observable behavior.

## Goals / Non-Goals

**Goals:**
- Keep public service and crypto calls independent of provider-specific SDKs and algorithms.
- Use a shared provider base abstraction with separate service and crypto contracts.
- Make provider choice configurable, with named providers and a default for each category.
- Keep raw service credentials, key material, and plaintext out of configuration and diagnostics.

**Non-Goals:**
- Third-party provider auto-discovery through package entry points.
- Service write, update, or delete operations.
- Asymmetric cryptography or crypto algorithms other than AES-GCM in the initial release.

## Decisions

- **Use a shared provider base class and specialized contracts.** `Provider` is the common base abstraction. `ServiceProvider(Provider)` defines the service retrieval contract, and `CryptoProvider(Provider)` defines the text encryption, decryption, and key-generation contract. Concrete implementations are `AzureKeyVaultProvider(ServiceProvider)` and `AESGCMProvider(CryptoProvider)`. The base carries shared provider identity and configuration behavior; category-specific operations remain on their respective subclasses. This avoids conflating the configured name chosen by a caller with the implementation class that performs the work.

- **Keep the facade focused on retrieval and provider lookup.** `KeySec` exposes `get_secret(secret, provider=None)` and `get_provider(name, provider_type=None)`, but does not expose `encrypt`, `decrypt`, or `generate_key`. `get_provider` resolves a configured provider name in the service or crypto category, instantiates its registered implementation with the configured settings, and returns that provider instance. `provider_type` optionally restricts lookup to `service` or `crypto`; when omitted, lookup checks both categories and reports an explicit ambiguity error if the same name is configured in both. Crypto operations remain methods on the returned `CryptoProvider`.

- **Separate API models and provider subpackages.** API-related classes reside under `src/keysec/model/`, with each class in a dedicated module except that all exception classes are centralized in `src/keysec/model/errors.py`. Service-provider contracts, registries, and implementations live under `src/keysec/providers/service/`; crypto-provider contracts, registries, and implementations live under `src/keysec/providers/crypto/`. Only shared provider infrastructure remains directly under `src/keysec/providers/`. Keep each non-error class in its own dedicated module, preserve the public `from keysec import KeySec` import, and remove redundant forwarding modules or packages rather than maintaining duplicate import paths.

- **Treat named provider configurations as the selection unit.** The YAML file is rooted at `keysec` and has `services` and `crypto` subsections, each containing a default provider name and a `providers` mapping. Each mapping key is the configured name; its entry contains an implementation `type` and provider-owned `settings`. For example:

  ```yaml
  keysec:
    services:
      default: vault
      providers:
        vault:
          type: azure-key-vault
          settings:
            vault_url: https://example.vault.azure.net/
    crypto:
      default: local
      providers:
        local:
          type: aes-gcm
          settings:
            key_file: ./keys/local.key
  ```

  `get_secret(..., provider=...)` selects a configured name from `keysec.services.providers`. `get_provider(name, provider_type=...)` selects a configured name from `keysec.services.providers` or `keysec.crypto.providers`; the category's default is used only when a category-specific operation omits its configured provider name, not for provider lookup by name. A type registry maps each implementation identifier to an in-process `ServiceProvider` or `CryptoProvider` class. Passing implementation objects directly from callers was rejected because it bypasses configuration and ties application code to adapter details.

- **Use YAML and explicit config discovery.** The application locates the unified file through `KEYSEC_CONFIG`, falling back to `./keysec.yaml` for no-argument `KeySec()` construction. YAML makes nested settings convenient to author but adds a parser dependency. The loader validates structure, configured names, defaults, implementation types, and provider-owned settings before operations.

- **Keep service credentials outside provider settings.** The Azure adapter uses ambient Azure identity, with workload or managed identity as appropriate. Service settings can identify credential references but do not contain raw credentials. Credentials, keys, plaintext, and retrieved secret values must not be written to logs or error messages.

- **Separate automatic provider tests from live-service checks.** Automatic service-provider tests use mocks or local test doubles and must never connect to remote services. Keep the sole live Azure Key Vault connectivity test in `tests/manual_azure_key_vault_integration.py`, outside default test discovery. Run it only by explicitly naming that file, with `KEYSEC_CONFIG` pointing to real configuration and `KEYSEC_TEST_SECRET_NAME` identifying a caller-provided test secret. The test verifies retrieval without printing or otherwise exposing the secret value.

- **Implement Azure Key Vault and AES-GCM as the initial concrete providers.** Azure SDK dependencies stay behind `AzureKeyVaultProvider`. `AESGCMProvider` uses AES-256-GCM, UTF-8 encodes input text, creates a fresh nonce per encryption, and returns a versioned URL-safe Base64 envelope containing the nonce and authenticated ciphertext. Authentication failure returns no plaintext. Keeping the envelope versioned allows format evolution while retaining string-only data values.

- **Use binary key files with provider-setting fallback.** Key generation writes a raw binary key to an explicit output path or the selected crypto provider's configured `key_file` setting and returns the destination path. Encrypt/decrypt accept an optional key-file path that overrides the configured setting. Key creation must not overwrite an existing file; restrictive file permissions are used where supported. This makes key ownership visible and avoids keeping key material in YAML or hidden in facade state.

## Risks / Trade-offs

- [YAML parsing adds a runtime dependency] -> Declare and test the parser dependency as part of the initial package metadata; reject malformed configuration with a clear configuration error.
- [Azure SDK authentication behavior varies by environment] -> Use the supported Azure identity chain and document the required vault permissions and local/workload identity setup.
- [A default config path can select the wrong file when applications run from an unexpected directory] -> Allow `KEYSEC_CONFIG` to identify the intended file explicitly and report the resolved path in configuration errors without exposing settings or secrets.
- [Key files can be exposed or lost] -> Create files without overwriting existing paths, restrict permissions where supported, and document that applications must protect and back up key files.
- [Ciphertext format changes can break decryption] -> Include a format version in the encoded AES-GCM envelope and test malformed, modified, and unsupported-version inputs.
- [Provider-specific failures can leak sensitive material if passed through unchecked] -> Preserve useful failure causes while ensuring diagnostics never include credentials, key material, or plaintext.

## Migration Plan

This is the initial package capability; there are no existing callers or configuration files to migrate. Add package metadata and the named service/crypto provider configuration alongside the implementations. Rollback consists of removing the new package capabilities and their configuration/dependency additions.
