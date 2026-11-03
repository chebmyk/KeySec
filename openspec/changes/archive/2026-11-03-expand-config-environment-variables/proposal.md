# Proposal

## Why

KeySec currently reads YAML values literally, so deployments cannot inject environment-provided values directly into provider configuration. Supporting `${NAME}` expansion lets operators configure sensitive or deployment-specific values such as Azure client secrets without hard-coding them in YAML, while preserving the existing configuration path and provider setup.

## What Changes

- Expand `${NAME}` references in string values throughout the loaded YAML document, including nested provider settings.
- Fail configuration loading explicitly when a referenced environment variable is unset.
- Treat an expanded Azure `client_secret` as the secret value itself; retain the existing environment-variable-name behavior for unwrapped literal values.
- Document the syntax, scope, and error behavior.

## Capabilities

### New Capabilities
- `configuration`: Environment-variable interpolation for string values in KeySec YAML configuration.

### Modified Capabilities
- `secret-retrieval`: Azure Key Vault service-principal authentication accepts an environment-expanded `client_secret` value directly, without interpreting it as another environment-variable name.

## Impact

- Configuration parsing in `src/keysec/config.py` and its tests.
- Azure Key Vault credential handling and its tests.
- Configuration guidance in `README.md`.
- No new runtime dependency or public API is required.
