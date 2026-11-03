# Spec Delta

## Purpose

Provides configurable, extensible authenticated encryption and key generation for text values through named crypto providers, without coupling callers to a particular cryptographic implementation.

## ADDED Requirements

### Requirement: Select a configured crypto provider
The system SHALL support multiple named crypto-provider configurations under `keysec.crypto.providers` in the YAML configuration and a configured default provider name under `keysec.crypto.default`. Each configuration SHALL identify a crypto-provider implementation type and provide its settings; callers MAY select a configured provider by name, and calls without a provider selection SHALL use the configured default.

#### Scenario: Use the configured default crypto provider
- **WHEN** a caller performs a crypto operation without specifying a provider and a default is configured
- **THEN** the system uses the configured default crypto provider

#### Scenario: Select a named crypto provider
- **WHEN** a caller performs a crypto operation and specifies a configured provider name
- **THEN** the system uses that crypto-provider configuration

#### Scenario: Reject an unknown crypto provider
- **WHEN** a caller specifies a crypto-provider name that is not configured
- **THEN** the system reports an explicit provider selection error without silently using another provider

#### Scenario: Require a default crypto provider
- **WHEN** a caller omits the provider name and no default crypto provider is configured
- **THEN** the system reports an explicit configuration error

### Requirement: Encrypt and decrypt text
`CryptoProvider` SHALL provide `encrypt(plaintext: str, key_file: str | None = None) -> str` and `decrypt(ciphertext: str, key_file: str | None = None) -> str`. Both operations SHALL use the provider instance's configured key file when no key-file override is supplied. The `KeySec` facade SHALL NOT expose these operations directly; callers obtain a configured crypto-provider instance with `KeySec.get_provider(name, provider_type="crypto")`.

#### Scenario: Encrypt and decrypt Unicode text
- **WHEN** a caller encrypts a plaintext string and decrypts the resulting ciphertext with the same provider and key
- **THEN** decryption returns the original plaintext string

#### Scenario: Reject invalid or unauthenticated ciphertext
- **WHEN** a caller decrypts malformed ciphertext or ciphertext that fails authentication
- **THEN** the system reports a decryption error and does not return plaintext

### Requirement: Generate and select binary key files
`CryptoProvider` SHALL provide `generate_key(output_path: str | None = None) -> str` to write cryptographic key material as a binary file at an explicit output path or the provider's configured key-file path. Encryption and decryption SHALL allow an explicit key-file path to override the provider's configured key file. The `KeySec` facade SHALL NOT expose key generation directly; callers obtain a configured crypto-provider instance with `KeySec.get_provider(name, provider_type="crypto")`.

#### Scenario: Generate a key at an explicit output path
- **WHEN** a caller generates a key and supplies an output path
- **THEN** the system writes the binary key to that path and returns the path

#### Scenario: Generate a key at the configured provider path
- **WHEN** a caller generates a key without an output path and the selected provider configures a key-file path
- **THEN** the system writes the binary key to the configured path and returns the path

#### Scenario: Reject key generation without a destination
- **WHEN** a caller generates a key without an output path and the selected provider has no configured key-file path
- **THEN** the system reports an explicit configuration error

#### Scenario: Use an explicit key-file override
- **WHEN** a caller supplies a key-file path to an encryption or decryption operation
- **THEN** the system uses that key file instead of the selected provider's configured key file

#### Scenario: Do not silently overwrite an existing key file
- **WHEN** key generation targets a path that already exists
- **THEN** the system reports a file-exists error and leaves the existing file unchanged

### Requirement: Use authenticated AES-GCM encryption
The system SHALL provide an AES-GCM crypto provider that authenticates encrypted data and returns ciphertext as a versioned URL-safe Base64 string containing the information required for decryption.

#### Scenario: Encrypt with AES-GCM
- **WHEN** a caller encrypts text using a configured AES-GCM provider and a valid key file
- **THEN** the provider UTF-8 encodes the text, uses a fresh nonce, and returns a versioned ciphertext string

#### Scenario: Reject modified AES-GCM ciphertext
- **WHEN** an AES-GCM ciphertext or its authentication data has been modified
- **THEN** decryption fails authentication and does not return plaintext

### Requirement: Extend crypto providers in process
The system SHALL allow an application to add a crypto-provider implementation in process and select it through a named provider configuration. The public `KeySec.get_provider` operation SHALL return an instance of the registered implementation so callers can use its crypto operations without adding crypto-operation methods to the `KeySec` facade.

#### Scenario: Use an added crypto provider
- **WHEN** an application registers an additional crypto provider and configures a named provider entry for it
- **THEN** `KeySec.get_provider` returns an instance of that implementation for the configured provider entry

### Requirement: Protect generated key files
The system SHALL avoid silently replacing existing key files and SHALL NOT include key material or plaintext values in diagnostics.

#### Scenario: Report a key-file or crypto failure safely
- **WHEN** key-file access or a crypto operation fails
- **THEN** the system reports the failure without exposing key material or plaintext in diagnostics
