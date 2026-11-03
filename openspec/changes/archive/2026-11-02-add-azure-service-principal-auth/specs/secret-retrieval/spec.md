# Spec Delta

## MODIFIED Requirements

### Requirement: Retrieve secrets from Azure Key Vault
The system SHALL provide a service provider that retrieves a named secret from the Azure Key Vault identified by its configured provider entry. The provider SHALL use ambient Azure identity when no service-principal credential settings are configured. For service-principal authentication, the provider settings SHALL specify `tenant_id`, `client_id`, and at least one of `client_secret` or `certificate_path`. `client_secret` SHALL identify an environment variable containing the secret, not contain the secret itself. When both credential settings are present, the provider SHALL use `certificate_path`.

#### Scenario: Retrieve a secret using ambient identity
- **WHEN** a caller selects an Azure Key Vault provider entry without `tenant_id`, `client_id`, `client_secret`, or `certificate_path` and requests an available secret
- **THEN** the provider retrieves the secret using the ambient Azure identity

#### Scenario: Authenticate a service principal with a client secret
- **WHEN** a caller configures `tenant_id`, `client_id`, and `client_secret` with the name of a set environment variable, and does not configure `certificate_path`
- **THEN** the provider authenticates using the environment-variable value without requiring the raw client secret in YAML

#### Scenario: Authenticate a service principal with a certificate
- **WHEN** a caller configures `tenant_id`, `client_id`, and `certificate_path` to an available unencrypted local certificate file
- **THEN** the provider authenticates using that certificate file without requiring certificate-password support

#### Scenario: Prefer certificate when both credential settings are present
- **WHEN** a caller configures both `client_secret` and `certificate_path` with otherwise valid service-principal settings
- **THEN** the provider authenticates using the certificate and does not read or use the client-secret environment variable

#### Scenario: Reject incomplete service-principal settings
- **WHEN** only one of `tenant_id` or `client_id` is configured, or service-principal identity is configured without either credential source
- **THEN** the provider reports an explicit configuration failure without falling back to ambient identity

#### Scenario: Reject unavailable selected credentials
- **WHEN** the selected client-secret environment variable is unset or the selected certificate file is unavailable
- **THEN** the provider reports an explicit configuration or authentication failure without exposing credential values or silently falling back to ambient identity

#### Scenario: Surface Azure Key Vault errors
- **WHEN** Azure Key Vault reports a missing secret, authorization failure, or service error
- **THEN** the retrieval operation reports the failure without returning a substitute value
