# Tasks

## 1. Package and shared configuration foundation

- [x] 1.1 Add Python package metadata, supported Python version, and runtime dependencies for YAML configuration, Azure Key Vault, and AES-GCM; verify package installation and import in a clean environment.
- [x] 1.2 Implement `KEYSEC_CONFIG` discovery with `./keysec.yaml` fallback and validation for the `keysec.services` and `keysec.crypto` sections, named providers, defaults, implementation types, and provider-owned settings; add tests for valid, malformed, missing, and invalid-default configurations and document the rooted YAML format.
- [x] 1.3 Keep API-related classes under `src/keysec/model/`, centralize all error classes in one `errors.py` module, and verify package imports and error compatibility.
- [x] 1.4 Organize service and crypto provider contracts, registries, and implementations into `src/keysec/providers/service/` and `src/keysec/providers/crypto/`; retain only shared provider infrastructure at the parent package, remove redundant forwarding modules/packages, update imports and tests, and run the complete suite.

## 2. Shared and service provider contracts

- [x] 2.1 Define the shared `Provider` base abstraction for configured provider identity and settings; verify service and crypto provider contracts can share it without mixing category-specific operations.
- [x] 2.2 Define `ServiceProvider(Provider)` and its in-process implementation-type registry; add a test provider and verify named service-provider selection.
- [x] 2.3 Implement `AzureKeyVaultProvider(ServiceProvider)` using configured vault settings and ambient Azure identity; add mocked tests for string values, missing secrets, authorization errors, and service errors.
- [x] 2.4 Document how applications register service-provider implementations and configure Azure identity and vault permissions; document the separate manual live-test invocation and verify the instructions match provider tests.
- [x] 2.5 Add the single manual-only live Azure Key Vault test in `tests/manual_azure_key_vault_integration.py`. Require `KEYSEC_CONFIG` and `KEYSEC_TEST_SECRET_NAME`, keep the file outside default test discovery, provide an explicit command to run it, and ensure the test never prints or exposes the retrieved value.

## 3. Crypto provider contract

- [x] 3.1 Define `CryptoProvider(Provider)` and its in-process implementation-type registry, including text encryption/decryption and binary key-file generation; add a test provider verifying registration and named provider selection.
- [x] 3.2 Document crypto-provider registration and named crypto-provider settings, and verify the documented extension flow with the test provider.

## 4. AES-GCM implementation and key files

- [x] 4.1 Implement AES-256-GCM with UTF-8 text handling and a versioned URL-safe Base64 ciphertext envelope; add tests for round-trip Unicode text, fresh nonces, tampering, malformed input, and unsupported envelope versions.
- [x] 4.2 Implement `AESGCMProvider(CryptoProvider)` binary key generation using configured provider paths or explicit overrides, and key-file selection for encryption/decryption; test key validity, no-overwrite behavior, path errors, and restrictive permissions where supported.
- [x] 4.3 Document AES-GCM provider settings, key-file protection, and key generation; verify examples use generated keys and explain ciphertext format compatibility.

## 5. Public facade and integration

- [x] 5.1 Implement `KeySec.get_secret(secret: str, provider: str | None = None) -> str` and `KeySec.get_provider(name: str, provider_type: str | None = None) -> Provider`; return configured service/crypto provider instances, report unknown or ambiguous lookups explicitly, remove crypto-operation methods from the facade, and test the public API.
- [x] 5.2 Verify integrated service and crypto behavior, including no fallback and no sensitive values in diagnostics; run the complete automatic test suite using only mocks or local test doubles, and verify it never connects to remote services. Keep the live Azure test opt-in and separate.
- [x] 5.3 Document the public facade with Azure secret retrieval and provider lookup examples; show crypto operations on a returned crypto-provider instance rather than on `KeySec`, and verify documented signatures.
