# Proposal

## Why

KeySec's CLI currently requires users to create configuration and use the Python API for encryption and decryption, leaving local cryptography cumbersome to try. A safe default configuration and CLI crypto commands will let users generate a key, encrypt values, and later decrypt them without writing a Python script, while retaining the existing secret and provider operations.

## What Changes

- Add a tracked root `keysec.yaml` with a default local AES-GCM crypto provider and key-file path. Include supported provider examples as comments, with no credentials or key material and no non-crypto provider enabled by default.
- Add installed `keysec encrypt` and `keysec decrypt` commands that accept a value as a positional argument or from standard input and use the default crypto provider unless another configured provider is named.
- Retain the `get-secret`, `generate-key`, `list-providers`, and `list-available-providers` subcommands.
- Let `get-secret` use the configured default service provider or an explicitly selected provider.
- Let `generate-key` use an explicitly named crypto provider or the configured default crypto provider, with an optional output path.
- Let `list-providers` show configured service and crypto providers, including their names and provider types without exposing settings or secret values.
- Let `list-available-providers` show registered service and crypto provider implementation types supported by the runtime API, independently of YAML configuration.
- Include clear usage examples in top-level and subcommand `--help` output.
- Write command results to standard output and operational errors to standard error with a non-zero exit status; never print key material or expose credentials in diagnostics.
- Document the default configuration, key generation, encryption/decryption, and all CLI commands, including the caution that positional values and plaintext output may be visible in shell history or captured output.

## Capabilities

### New Capabilities
- `command-line-interface`: Installed command-line operations for secret retrieval, key generation, encryption/decryption, provider listing, and using a safe default local crypto configuration.

### Modified Capabilities
- None.

## Impact

- Tracked root `keysec.yaml` and `.gitignore` handling for that safe default file.
- Python package script entry point and CLI implementation.
- Existing `KeySec.get_secret`, `KeySec.get_provider`, and `CryptoProvider.generate_key` APIs.
- CLI tests and README usage documentation for all commands and default configuration.
- No new runtime dependency is expected; the standard-library argument parser is sufficient.
