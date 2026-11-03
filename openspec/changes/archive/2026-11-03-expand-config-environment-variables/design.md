# Design

## Context

`load_config` currently parses the YAML document with `yaml.safe_load` and immediately validates the resulting `keysec` mapping. Azure Key Vault currently interprets a plain `client_secret` string as the name of an environment variable; decrypted wrapped strings use a marker subclass so they can be passed directly to Azure authentication.

See `proposal.md` for motivation and the spec deltas for required behavior.

## Goals / Non-Goals

**Goals:**
- Resolve `${NAME}` placeholders in parsed YAML string values before provider configuration validation.
- Preserve the source distinction needed for Azure to use expanded values as literals without changing legacy plain-string behavior.
- Report missing variables without including environment-variable contents in errors.

**Non-Goals:**
- Supporting shell expansion forms such as `$NAME`, `${NAME:-default}`, or command substitution.
- Expanding YAML mapping keys or values introduced by a substituted value.
- Changing how `KEYSEC_CONFIG` selects the YAML file.

## Decisions

- **Walk parsed configuration values recursively.** Expand string values in mappings and lists, leaving keys and non-string values unchanged. This reuses the existing YAML parser and avoids a second parsing stage.
- **Substitute only placeholders present in the parsed YAML.** Environment values are inserted as literal strings and are not recursively expanded or interpreted as YAML. A missing variable raises `ConfigurationError`; the diagnostic may identify the variable name but must not include its value.
- **Mark expanded string values.** Use a dedicated `str` subclass or equivalent typed marker so the Azure provider can pass an expanded `client_secret` directly to credential construction. Keep existing unmarked plain strings as environment-variable names and preserve the existing marker used for decrypted values. Do not rely on truthiness or guessing based on whether the text happens to match a defined environment variable.
- **Keep parsing and validation order explicit.** Parse YAML first, perform one interpolation pass over its values, then run the existing root/group/provider validation. This prevents substituted text from introducing YAML keys, mappings, or scalar types.

## Risks / Trade-offs

- [Environment-provided strings may contain secret material] → Never include substituted contents in configuration errors or diagnostics; tests should assert safe error messages.
- [A literal `${NAME}` may be intended as data] → Treat this syntax as interpolation by contract; users needing a literal placeholder must avoid that form or use another representation.
- [Empty environment variables are set but may not be valid provider settings] → Substitute the empty string and let the existing configuration validation reject it where a non-empty value is required.

## Migration Plan

No file-format migration is required. Existing plain Azure `client_secret` values remain environment-variable names; `${NAME}` explicitly opts into expansion to the variable's value. Rollback consists of removing `${...}` references and returning to literal values.
