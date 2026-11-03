# Proposal

## Why

Applications that cannot use an ambient Azure identity need a simple way to authenticate KeySec to Azure Key Vault as a service principal. Direct provider settings for tenant/client identity and a client-secret environment-variable name or local certificate path make configuration simpler without placing raw secrets in YAML.

## What Changes

- Extend the Azure Key Vault provider to support service-principal settings directly in the provider settings: `tenant_id`, `client_id`, and either `client_secret` (the name of an environment variable) or `certificate_path` (an unencrypted local certificate file).
- When both `client_secret` and `certificate_path` are configured, use the certificate.
- Preserve the existing ambient Azure identity behavior when service-principal authentication is not configured.
- Validate service-principal settings and surface authentication failures without exposing credentials or secret values.
- Document the simplified configuration shape and credential-source requirements.

## Capabilities

### New Capabilities

### Modified Capabilities
- `secret-retrieval`: Define Azure Key Vault authentication behavior for ambient identity and service principals using a client-secret environment-variable name or a local certificate path, with certificate precedence when both are set.

## Impact

- Affects `AzureKeyVaultProvider` configuration, credential construction, provider tests, and Azure setup documentation.
- Uses the existing `azure-identity` dependency; no new runtime dependency is expected.
- Client-secret values remain outside YAML; the `client_secret` setting names an environment variable. Client-certificate authentication uses a local file path and does not support a certificate password in this change.
