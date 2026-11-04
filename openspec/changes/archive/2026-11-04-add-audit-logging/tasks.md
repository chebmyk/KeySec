# Tasks

## 1. Audit Configuration

- [x] 1.1 Extend the validated configuration model and YAML loader with optional `keysec.audit_logging.enabled` and `file` settings, retaining the specified defaults and validation errors; verify configuration tests cover absent settings, custom paths, environment expansion, and invalid values.
- [x] 1.2 Update `keysec.yaml` and the README with an opt-in audit logging example; verify the documented YAML shape matches the loader and the checked-in default remains valid with logging disabled.

## 2. Audit Log Handler

- [x] 2.1 Implement the dedicated audit logger with daily file rotation, metadata-only formatting, no root-logger configuration, and a reported-but-non-blocking write failure path; verify disabled logging does not create a file and an unavailable destination does not disrupt an operation.
- [x] 2.2 Add focused logger tests for daily rollover, preservation of prior files, event metadata, and failure reporting; verify the tests pass without emitting secret or operation payload data.

## 3. Operation Instrumentation

- [x] 3.1 Implement a reusable `@audit` decorator and apply it directly to `KeySec.get_secret` and crypto-provider encrypt, decrypt, and key-generation methods, sourcing the active logger and provider identity from configured audit context; verify signatures, arguments, results, exceptions, custom providers, success/failure outcomes, and exclusion of secret names, values, plaintext, ciphertext, and key material.

## 4. Integration Verification

- [x] 4.1 Run the targeted configuration, API, CLI, and audit logger tests together and `openspec validate add-audit-logging --type change`; verify all tests pass and every required artifact validates.
