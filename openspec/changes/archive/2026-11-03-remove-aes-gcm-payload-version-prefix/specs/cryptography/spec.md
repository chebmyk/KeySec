# Spec Delta

## MODIFIED Requirements

### Requirement: Use authenticated AES-GCM encryption
The system SHALL provide an AES-GCM crypto provider that authenticates encrypted data and returns a configured-prefix wrapper around a URL-safe Base64 payload containing the information required for decryption. Newly encrypted payloads SHALL contain the nonce followed by AES-GCM ciphertext and its authentication tag, without an internal textual version marker.

#### Scenario: Encrypt with AES-GCM
- **WHEN** a caller encrypts text using a configured AES-GCM provider and a valid key file
- **THEN** the provider UTF-8 encodes the text, uses a fresh nonce, and returns a configured-prefix-wrapped URL-safe Base64 payload containing the nonce, ciphertext, and authentication tag without an internal version prefix

#### Scenario: Decrypt the new AES-GCM payload
- **WHEN** a caller decrypts a newly generated wrapped AES-GCM payload with the same provider and key
- **THEN** the provider returns the original plaintext

#### Scenario: Reject malformed inner payload
- **WHEN** a caller decrypts a wrapped or unwrapped value whose inner payload is not valid URL-safe Base64
- **THEN** the provider reports a malformed or unsupported ciphertext error without returning plaintext

#### Scenario: Reject modified AES-GCM ciphertext
- **WHEN** an AES-GCM ciphertext or its authentication data has been modified
- **THEN** decryption fails authentication and does not return plaintext
