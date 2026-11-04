# Audit Logging Specification

## Purpose

Provides operators with a durable, privacy-preserving record of secret retrieval and cryptographic operations performed through KeySec.

## Requirements

### Requirement: Record audit metadata for supported operations
When audit logging is enabled, the system SHALL record secret retrieval, encryption, decryption, and key-generation outcomes with operation metadata and the outcome.

#### Scenario: Record successful operations
- **WHEN** a supported operation completes successfully
- **THEN** the audit entry identifies the operation, provider, event timestamp, and successful outcome

#### Scenario: Record failed operations
- **WHEN** a supported operation fails
- **THEN** the audit entry identifies the operation, provider when available, event timestamp, and failed outcome without including exception text

### Requirement: Exclude secrets and operation payloads from audit entries
Audit entries SHALL contain no secret names, secret values, plaintext, ciphertext, or other operation payloads.

#### Scenario: Audit secret retrieval
- **WHEN** KeySec retrieves a secret
- **THEN** the audit entry records the operation outcome without recording the requested secret name or returned secret value

#### Scenario: Audit cryptographic operations
- **WHEN** KeySec encrypts, decrypts, or generates a key
- **THEN** the audit entry records the operation outcome without recording plaintext, ciphertext, or key material

### Requirement: Rotate audit logs daily
When audit logging is enabled, the system SHALL rotate its audit log file daily while preserving prior log files.

#### Scenario: Daily log rotation
- **WHEN** the audit log reaches its daily rotation boundary
- **THEN** subsequent audit entries are written to a new log file and the previous file remains available

### Requirement: Continue operations when audit writes fail
Failure to write an audit entry SHALL NOT change the result of the corresponding application operation, and the logging failure SHALL be reported through standard Python logging.

#### Scenario: Audit file is unavailable
- **WHEN** a supported operation completes but its audit entry cannot be written
- **THEN** the operation retains its normal result and the audit logging failure is reported separately

### Requirement: Keep audit logging inactive unless configured
Audit logging SHALL produce no audit entries when it is disabled or omitted from configuration.

#### Scenario: Audit logging is not enabled
- **WHEN** the audit logging configuration is absent or disabled
- **THEN** supported operations continue without creating an audit log file or writing audit entries
