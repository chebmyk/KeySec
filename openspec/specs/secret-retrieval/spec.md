# Secret Retrieval Specification

## Purpose

Provides Python applications a consistent, configurable way to retrieve named secrets as strings without coupling callers to a particular secrets service.

## Requirements

### Requirement: Select a configured service provider
The system SHALL support multiple named service-provider configurations under `keysec.services.providers` in the YAML configuration and a configured default provider name under `keysec.services.default`. Each configuration SHALL identify a service-provider implementation type and provide its settings; callers MAY select a configured provider by name, and calls without a provider selection SHALL use the configured default.

#### Scenario: Use the configured default provider
- **WHEN** a caller retrieves a secret without specifying a provider and a default is configured
- **THEN** the system retrieves the secret using the configured default provider

#### Scenario: Select a named provider
- **WHEN** a caller retrieves a secret and specifies a configured provider name
- **THEN** the system retrieves the secret using that provider configuration

#### Scenario: Reject an unknown provider
- **WHEN** a caller specifies a provider name that is not configured
- **THEN** the system reports an explicit provider selection error without silently using another provider

#### Scenario: Require a default when no provider is selected
- **WHEN** a caller omits the provider name and no default provider is configured
- **THEN** the system reports an explicit configuration error

### Requirement: Retrieve secrets through the public API
The system SHALL expose a `KeySec` public facade whose `get_secret` operation accepts a secret name as a string and an optional configured service-provider name, and returns the retrieved secret value as a string.

#### Scenario: Retrieve a string secret
- **WHEN** a caller requests an existing secret through a configured service provider
- **THEN** the operation returns that secret's value as a string

#### Scenario: Report a missing secret
- **WHEN** the selected service reports that the requested secret does not exist
- **THEN** the operation reports the retrieval failure and does not return a substitute value

#### Scenario: Report a service or authentication failure
- **WHEN** the selected service provider cannot retrieve a secret because of a service or authentication failure
- **THEN** the operation surfaces the failure and does not silently fall back to another provider

### Requirement: Look up a configured provider
The system SHALL expose `KeySec.get_provider(name: str, provider_type: str | None = None) -> Provider` to return an instance of the implementation registered for the named configured provider. When `provider_type` is `service`, the system SHALL search `keysec.services.providers`; when it is `crypto`, the system SHALL search `keysec.crypto.providers`. When omitted, the system SHALL search both categories and SHALL report an explicit ambiguity error if the same configured name exists in both. The operation SHALL report an explicit error for an unknown provider name or provider type.

#### Scenario: Look up a configured service provider
- **WHEN** a caller requests a configured service provider by name and selects the service category or the name is unique across categories
- **THEN** the system returns an instance of the registered implementation initialized with that provider's configured settings

#### Scenario: Reject ambiguous provider lookup
- **WHEN** a caller omits `provider_type` and the requested name is configured in both service and crypto categories
- **THEN** the system reports an explicit ambiguity error

#### Scenario: Reject unknown provider lookup
- **WHEN** a caller requests a provider name or category that is not configured
- **THEN** the system reports an explicit provider lookup error

### Requirement: Keep raw credentials out of configuration
The system SHALL support service authentication through ambient identity or credential references and SHALL NOT require raw credential values to be stored in service-provider settings.

#### Scenario: Configure a provider without inline credentials
- **WHEN** an operator configures a service provider
- **THEN** its settings contain provider configuration and, when needed, credential references rather than raw credentials

### Requirement: Extend service providers in process
The system SHALL allow an application to add a service-provider implementation in process and select it through a named provider configuration without changing the public secret-retrieval API.

#### Scenario: Use an added provider
- **WHEN** an application registers an additional service provider and configures a named provider entry for it
- **THEN** the public retrieval operation can use that provider entry to retrieve a secret

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
