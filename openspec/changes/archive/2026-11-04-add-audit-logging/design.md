# Design

## Context

Configuration is loaded and validated in `keysec.config`, then represented by `KeySecConfig`. The `KeySec` facade handles secret retrieval and returns concrete provider instances; the CLI invokes crypto methods on those same instances. See proposal.md for motivation and the spec deltas for behavior.

## Goals / Non-Goals

**Goals:**
- Keep the implementation on Python's standard `logging` APIs, without adding a dependency.
- Preserve existing provider instance identity and operation signatures.
- Keep audit configuration and file handling isolated from application/root logger configuration.

**Non-Goals:**
- Add audit events for configuration inspection, provider listing, or unrelated application diagnostics.
- Change the public API to add top-level encrypt, decrypt, or key-generation methods.

## Decisions

- **Use a dedicated audit logger and a daily rotating file handler.** Use `TimedRotatingFileHandler` with a one-day interval and a formatter containing only the operation metadata allowed by the spec. Do not call `basicConfig` or attach handlers to the root logger. A custom handler error path must report write failures through standard Python logging without allowing them to change operation results. This uses the standard library and keeps audit output separate from application diagnostics; a third-party logging package or the root logger would add dependency or configuration coupling.
- **Add validated settings under `keysec.audit_logging`.** Parse an optional mapping in the existing configuration loader. Default `enabled` to false and `file` to `./audit.log`; let existing environment-variable expansion apply to the path. Do not create or open the audit file when logging is disabled. This preserves current behavior for existing configurations and follows the current configuration model rather than introducing a second configuration source.
- **Use a reusable `@audit` decorator on supported operations.** Apply it directly to `KeySec.get_secret` and the crypto provider methods for `encrypt`, `decrypt`, and `generate_key`, rather than wrapping methods in `KeySec.get_provider`. The decorator obtains the active audit logger and provider identity from the operation's configured audit context, records only the operation outcome and permitted metadata, and preserves the wrapped method's signature, return value, and exceptions. With audit logging disabled, decorated methods proceed without creating a log file or writing audit entries. The CLI already calls these methods, so it should not add duplicate event emission.
- **Log outcomes without operation data.** Format entries from a fixed set of fields: operation, provider identity when available, timestamp, and success/failure. Do not pass arguments, results, exception messages, or key material to the audit logger.

## Risks / Trade-offs

- [Audit logging can fail because the destination is unavailable or unwritable] → Report failures through the separate standard logging error path and continue the underlying operation, as required by the spec.
- [Applying the decorator across facade and provider methods can affect custom provider implementations] → Keep the decorator generic, preserve wrapped signatures, arguments, return values, raised exceptions, and provider identity, and test with custom providers as well as methods called without audit logging enabled.
- [Daily rotation can leave many files over time] → Preserve rotated files as specified; configurable retention is outside this change.

## Migration Plan

Existing YAML configurations remain valid and keep audit logging disabled. To enable it, add `keysec.audit_logging.enabled: true` and optionally set `keysec.audit_logging.file`. Rollback consists of removing or disabling that section; no data migration or dependency change is required.
