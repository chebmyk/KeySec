# Proposal

## Why

KeySec currently exposes secret retrieval and crypto key generation only through its Python API, requiring a Python caller or a separate script for routine operational tasks. A small installed command-line interface will let operators retrieve configured secrets, create provider key files, inspect configured provider names, and discover registered provider implementations.

## What Changes

- Add an installed `keysec` command with `get-secret`, `generate-key`, `list-providers`, and `list-available-providers` subcommands.
- Let `get-secret` use the configured default service provider or an explicitly selected provider.
- Let `generate-key` use an explicitly named crypto provider or the configured default crypto provider, with an optional output path.
- Let `list-providers` show configured service and crypto providers, including their names and provider types without exposing settings or secret values.
- Let `list-available-providers` show registered service and crypto provider implementation types supported by the runtime API, independently of YAML configuration.
- Include clear usage examples in the command and subcommand `--help` output.
- Write the retrieved secret, generated key-file path, or configured provider metadata to standard output; report operational errors to standard error with a non-zero exit status.
- Document command syntax and examples without printing key material or exposing credentials in diagnostics.

## Capabilities

### New Capabilities
- `command-line-interface`: Installed command-line operations for retrieving a secret, generating a crypto-provider key file, and listing configured providers and registered provider implementations.

### Modified Capabilities

## Impact

- Python package script entry point and CLI implementation.
- Existing `KeySec.get_secret`, `KeySec.get_provider`, and `CryptoProvider.generate_key` APIs.
- CLI tests and README usage documentation for all commands.
- No new runtime dependency is expected; the standard-library argument parser is sufficient.
