# Spec Delta

## ADDED Requirements

### Requirement: Configure audit logging through YAML
The system SHALL accept optional audit logging settings under `keysec.audit_logging`, with an `enabled` boolean defaulting to false and a non-empty `file` path defaulting to `./audit.log`.

#### Scenario: Omit audit logging settings
- **WHEN** `keysec.audit_logging` is omitted
- **THEN** configuration loads with audit logging disabled and the default audit log path

#### Scenario: Configure an audit log file
- **WHEN** `keysec.audit_logging` contains `enabled: true` and a non-empty `file` path
- **THEN** the validated configuration enables audit logging and exposes the configured path

#### Scenario: Reject invalid audit logging settings
- **WHEN** audit logging settings are not a mapping, `enabled` is not a boolean, or `file` is empty or not a string
- **THEN** configuration loading fails with an explicit configuration error
