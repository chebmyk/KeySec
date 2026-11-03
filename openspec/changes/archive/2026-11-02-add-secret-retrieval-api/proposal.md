# Proposal

## Why

Python applications need consistent APIs for retrieving secrets and performing authenticated encryption without coupling application code to a specific service or algorithm. KeySec will provide configurable named service and crypto providers behind one extensible public facade.

## What Changes

- Add a public `KeySec` facade with `get_secret(secret: str, provider: str | None = None) -> str` and `get_provider(name: str, provider_type: str | None = None) -> Provider`.
- Expose text encryption, decryption, and key generation through configured crypto-provider instances returned by `get_provider`, rather than as `KeySec` facade methods.
- Add unified YAML configuration rooted at `keysec`, with `services` and `crypto` subsections for named providers, defaults, implementation types, and provider-specific settings.
- Add a shared `Provider` abstraction with `ServiceProvider` and `CryptoProvider` specializations, plus Azure Key Vault and AES-GCM implementations.
- Keep API-related classes in the model package, centralize all error classes in one module, and organize service and crypto providers in separate subpackages with dedicated class modules; remove redundant forwarding modules and packages.
- Keep raw service credentials out of configuration; use credential references or ambient authentication. Generate crypto keys as binary files.

## Capabilities

### New Capabilities
- `secret-retrieval`: Retrieve named secrets as strings through configurable service providers.
- `cryptography`: Encrypt and decrypt text and generate binary key files through configurable crypto providers.

### Modified Capabilities

## Impact

- Establishes the Python package's initial public APIs, configuration contract, and provider extension points.
- Adds YAML parsing, Azure Key Vault, and cryptography dependencies and their associated identity/key-file setup.
- The repository has no existing package source, tests, or capability specs; implementation conventions and compatibility constraints must be established as part of this initial capability.
