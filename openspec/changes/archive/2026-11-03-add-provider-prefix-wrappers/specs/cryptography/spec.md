# Spec Delta

## MODIFIED Requirements

### Requirement: Encrypt and decrypt text
`CryptoProvider` SHALL provide `encrypt(plaintext: str, key_file: str | None = None) -> str` and `decrypt(ciphertext: str, key_file: str | None = None) -> str`. Both operations SHALL use the provider instance's configured key file when no key-file override is supplied. The `KeySec` facade SHALL NOT expose these operations directly; callers obtain a configured crypto-provider instance with `KeySec.get_provider(name, provider_type="crypto")`. Encryption SHALL return ciphertext wrapped with the provider's effective cipher prefix, inherited from `keysec.crypto.cipher_prefix` unless overridden in that provider's settings. Decryption SHALL accept the wrapped form and existing unwrapped ciphertext.

#### Scenario: Encrypt and decrypt Unicode text
- **WHEN** a caller encrypts a plaintext string and decrypts the resulting ciphertext with the same provider and key
- **THEN** decryption returns the original plaintext string

#### Scenario: Reject invalid or unauthenticated ciphertext
- **WHEN** a caller decrypts malformed ciphertext or ciphertext that fails authentication
- **THEN** the system reports a decryption error and does not return plaintext

#### Scenario: Wrap ciphertext with the configured provider prefix
- **WHEN** a caller encrypts text using a provider with the default or an overridden cipher prefix
- **THEN** the returned string uses the format `<prefix>(<ciphertext>)`, with the default prefix `ENC`

#### Scenario: Decrypt legacy unwrapped ciphertext
- **WHEN** a caller decrypts ciphertext in the provider's existing unwrapped format
- **THEN** decryption returns the original plaintext

### Requirement: Use authenticated AES-GCM encryption
The system SHALL provide an AES-GCM crypto provider that authenticates encrypted data and returns a configured-prefix wrapper around a versioned URL-safe Base64 ciphertext containing the information required for decryption.

#### Scenario: Encrypt with AES-GCM
- **WHEN** a caller encrypts text using a configured AES-GCM provider and a valid key file
- **THEN** the provider UTF-8 encodes the text, uses a fresh nonce, and returns a configured-prefix-wrapped versioned ciphertext string

#### Scenario: Reject modified AES-GCM ciphertext
- **WHEN** an AES-GCM ciphertext or its authentication data has been modified
- **THEN** decryption fails authentication and does not return plaintext

## ADDED Requirements

### Requirement: Configure the crypto category cipher prefix
The crypto category SHALL use `ENC` as its default cipher prefix and SHALL allow a non-empty `keysec.crypto.cipher_prefix` value to override that default. A crypto provider MAY override the category prefix with a non-empty `cipher_prefix` setting.

#### Scenario: Use the default category cipher prefix
- **WHEN** the crypto category and provider are configured without a cipher-prefix override
- **THEN** its encrypted output uses `ENC` as the wrapper prefix

#### Scenario: Override the category cipher prefix
- **WHEN** `keysec.crypto.cipher_prefix` is set to a non-empty prefix and the provider has no override
- **THEN** the provider's encrypted output and accepted wrapped input use the category prefix

#### Scenario: Override the category prefix for one crypto provider
- **WHEN** a crypto provider has a non-empty `cipher_prefix` setting
- **THEN** that provider's encrypted output and accepted wrapped input use its setting instead of the category prefix

#### Scenario: Reject an invalid cipher prefix
- **WHEN** a category or provider cipher-prefix value is empty or not a string
- **THEN** the system reports an explicit configuration error

### Requirement: Decrypt wrapped provider setting values
The system SHALL decrypt string values in provider settings that use the effective cipher prefix for their category or provider, using the configured default crypto provider. Prefix controls and the default crypto provider's bootstrap settings SHALL remain plaintext.

#### Scenario: Resolve an encrypted crypto provider setting
- **WHEN** a crypto provider setting contains a value wrapped with that provider's effective cipher prefix
- **THEN** the system removes the wrapper and decrypts the value using the configured default crypto provider before initializing the provider

#### Scenario: Resolve an encrypted service provider setting
- **WHEN** a service provider setting contains a value wrapped with that provider's effective cipher prefix
- **THEN** the system removes the wrapper and decrypts the value using the configured default crypto provider before initializing the provider

#### Scenario: Leave unwrapped provider settings unchanged
- **WHEN** a provider setting does not use its effective cipher prefix wrapper
- **THEN** the system passes the setting value through unchanged

#### Scenario: Report missing default crypto configuration
- **WHEN** a provider setting uses a cipher-prefix wrapper and no default crypto provider is configured
- **THEN** the system reports an explicit configuration error

#### Scenario: Report a configuration decryption failure
- **WHEN** a wrapped provider setting cannot be decrypted
- **THEN** the system reports an explicit error and does not fall back to another interpretation of the value
