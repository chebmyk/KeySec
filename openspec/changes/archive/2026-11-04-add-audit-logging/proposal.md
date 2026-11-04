# Proposal

## Why

KeySec currently has no durable record of secret retrieval or cryptographic operations. A configurable audit trail will help operators review these actions without exposing secret names or payload data.

## What Changes

- Add an opt-in audit logger configured through the KeySec YAML configuration.
- Record secret retrieval and encrypt, decrypt, and key-generation outcomes with operation metadata only; never record secret names, secrets, plaintext, or ciphertext.
- Rotate audit log files daily.
- Keep audit logging disabled when it is not explicitly enabled, and allow application operations to continue if writing an audit entry fails while reporting the logging failure.

## Capabilities

### New Capabilities
- `audit-logging`: Configurable, privacy-preserving audit records for secret retrieval and cryptographic operations, with daily log rotation.

### Modified Capabilities
- `configuration`: Add validated configuration for enabling and setting up audit logging.

## Impact

- Extends YAML configuration loading and its validated model.
- Adds audit logging setup and instrumentation to the KeySec facade and crypto-provider operations used through the API and CLI.
- Updates configuration, API, and CLI tests and the example configuration.
