# Configuration Specification

## Purpose

Allows deployments to supply configuration values through environment variables while keeping environment-specific and sensitive values out of YAML files.

## Requirements

### Requirement: Expand environment variables in YAML string values
The system SHALL replace `${NAME}` references in YAML string values with the corresponding environment-variable values when loading configuration.

#### Scenario: Expand a complete string value
- **WHEN** a YAML string value consists of `${NAME}` and `NAME` is set in the process environment
- **THEN** the loaded configuration contains the environment-variable value

#### Scenario: Expand references within and across values
- **WHEN** one or more `${NAME}` references appear in a string, including in nested mappings or lists, and all referenced variables are set
- **THEN** each reference in each string value is replaced, while YAML mapping keys and non-string values remain unchanged

#### Scenario: Keep substituted values literal
- **WHEN** an environment-variable value itself contains text matching `${NAME}`
- **THEN** the substituted text is not expanded again

#### Scenario: Reject an unset environment variable
- **WHEN** a YAML string value references an environment variable that is not set
- **THEN** configuration loading fails with an explicit configuration error and does not accept the unresolved placeholder as a value

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
