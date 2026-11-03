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
