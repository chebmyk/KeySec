# Spec Delta

## Purpose

Provides operators with command-line access to KeySec's configured secret retrieval, crypto key-generation, and provider-listing operations without requiring a Python script.

## ADDED Requirements

### Requirement: Retrieve a secret from the command line
The installed `keysec` command SHALL provide a `get-secret` operation that retrieves a named secret through the configured service provider.

#### Scenario: Retrieve using the default service provider
- **WHEN** a caller runs `keysec get-secret SECRET` and a default service provider is configured
- **THEN** the command prints the retrieved secret value to standard output

#### Scenario: Select a service provider
- **WHEN** a caller runs `keysec get-secret SECRET --provider NAME`
- **THEN** the command retrieves the secret using the named configured service provider

#### Scenario: Report secret retrieval errors
- **WHEN** configuration, provider selection, or secret retrieval fails
- **THEN** the command reports an error to standard error, returns a non-zero exit status, and does not print a substitute secret value

### Requirement: Generate a crypto-provider key from the command line
The installed `keysec` command SHALL provide a `generate-key` operation that generates a key using the configured default crypto provider or a named configured crypto provider, with an optional output path.

#### Scenario: Generate a key using the default crypto provider
- **WHEN** a caller runs `keysec generate-key` and a default crypto provider with a configured key-file path exists
- **THEN** the command creates the key file through that provider and prints its path to standard output

#### Scenario: Report a missing default crypto provider
- **WHEN** a caller runs `keysec generate-key [--output PATH]` without `--provider` and no default crypto provider is configured
- **THEN** the command reports an error to standard error, returns a non-zero exit status, and does not generate a key

#### Scenario: Generate a key at the provider's configured path
- **WHEN** a caller runs `keysec generate-key --provider NAME` and the provider has a configured key-file path
- **THEN** the command creates the key file through that provider and prints its path to standard output

#### Scenario: Generate a key at an explicit path
- **WHEN** a caller runs `keysec generate-key --provider NAME --output PATH`
- **THEN** the command creates the key file at the requested path and prints that path to standard output

#### Scenario: Select a crypto provider explicitly
- **WHEN** a caller runs `keysec generate-key --provider NAME` while a different default crypto provider is configured
- **THEN** the command generates the key using the named provider instead of the default

#### Scenario: Avoid overwriting an existing key file
- **WHEN** the requested or configured output path already exists
- **THEN** the command reports an error to standard error, returns a non-zero exit status, and leaves the existing file unchanged

#### Scenario: Report key-generation errors without exposing key material
- **WHEN** configuration, provider selection, or key generation fails
- **THEN** the command reports an error to standard error, returns a non-zero exit status, and does not print key material

### Requirement: List configured providers from the command line
The installed `keysec` command SHALL provide a `list-providers` operation that lists providers configured in the KeySec configuration without exposing provider settings or secret values.

#### Scenario: List configured service and crypto providers
- **WHEN** a caller runs `keysec list-providers`
- **THEN** the command prints each configured provider's category, name, and provider type to standard output

#### Scenario: No providers are configured
- **WHEN** a caller runs `keysec list-providers` and no service or crypto providers are configured
- **THEN** the command prints `No providers configured.` to standard output

#### Scenario: Provider listing does not expose settings
- **WHEN** a caller runs `keysec list-providers`
- **THEN** the command does not print provider settings, credentials, or secret values

### Requirement: List available provider implementations from the command line
The installed `keysec` command SHALL provide a `list-available-providers` operation that lists service and crypto provider implementation types registered with the runtime API, whether or not they appear in the KeySec configuration.

#### Scenario: List implementations registered with the runtime API
- **WHEN** a caller runs `keysec list-available-providers`
- **THEN** the command prints each registered provider implementation's category and implementation type to standard output

#### Scenario: Available provider listing is independent of configuration
- **WHEN** a caller runs `keysec list-available-providers` without a KeySec configuration file
- **THEN** the command still lists implementations registered by the runtime API

#### Scenario: No provider implementations are registered
- **WHEN** a caller runs `keysec list-available-providers` and no implementations are registered
- **THEN** the command prints `No provider implementations available.` to standard output

#### Scenario: Available provider listing does not expose configuration
- **WHEN** a caller runs `keysec list-available-providers`
- **THEN** the command does not read or print provider configuration, settings, credentials, or secret values

### Requirement: Show command examples in help
The installed `keysec` command SHALL show clear usage and at least one valid example for each operation in its help output.

#### Scenario: Show examples in top-level help
- **WHEN** a caller runs `keysec --help`
- **THEN** the help output describes `get-secret`, `generate-key`, `list-providers`, and `list-available-providers` and includes a valid example for each

#### Scenario: Show examples in subcommand help
- **WHEN** a caller runs `keysec <COMMAND> --help` for any supported command
- **THEN** the help output includes the command's usage and a valid example

### Requirement: Use the standard KeySec configuration source for configured operations
The `get-secret`, `generate-key`, and `list-providers` operations SHALL use the same configuration file selection and provider configuration as the KeySec Python API.

#### Scenario: Honor the configured configuration file
- **WHEN** `KEYSEC_CONFIG` names a configuration file
- **THEN** `get-secret`, `generate-key`, and `list-providers` use that file

#### Scenario: Use the default configuration file
- **WHEN** `KEYSEC_CONFIG` is unset
- **THEN** `get-secret`, `generate-key`, and `list-providers` use `./keysec.yaml`
