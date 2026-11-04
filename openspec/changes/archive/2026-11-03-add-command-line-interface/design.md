# Design

## Context

The package exports `KeySec`, whose `get_secret` method already supports the configured default service provider and named overrides. Configured providers and the crypto group's default are available through the loaded configuration; crypto providers expose `generate_key(output_path)`. `pyproject.toml` uses setuptools and currently declares no console scripts or CLI dependencies.

See `proposal.md` for motivation and the spec delta for the command contract.

## Goals / Non-Goals

**Goals:**
- Keep the CLI a thin adapter around existing public APIs so configuration selection, wrapper parsing, provider validation, and key-file safety remain consistent.
- Provide a ready-to-use local AES-GCM configuration when running from the repository root without `KEYSEC_CONFIG`.
- Support CLI encryption and decryption using either positional input or standard input.
- List configured providers by category, name, and provider type without instantiating them or exposing settings.
- List runtime-registered provider implementation types separately from configuration, without requiring a KeySec configuration file.
- Make the commands available after installing the package.
- Include valid, task-oriented examples in top-level and subcommand help.
- Keep command results clear and send operational diagnostics to standard error.

**Non-Goals:**
- Add interactive configuration editing or alternate configuration formats.
- Change the Python API or provider behavior.

## Decisions

- **Use `argparse` and a setuptools console script.** This avoids a runtime dependency and exposes the conventional installed `keysec` command. A `python -m`-only interface was considered but would not provide the requested installed command directly.
- **Delegate secret retrieval to `KeySec.get_secret`.** `get-secret` accepts a positional secret name and an optional `--provider`; omitting the option naturally uses the configured default service provider.
- **Default key generation to the configured crypto provider.** `generate-key --provider NAME` selects the named crypto provider; when `--provider` is omitted, the command selects the configured default crypto provider. If no default is configured, it reports an error and does not generate a key. `--output PATH` is optional and is passed through to the selected provider, which otherwise uses its configured key-file path.
- **Ship a safe root `keysec.yaml`.** Configure only the `local` AES-GCM crypto provider as default, with a relative local key-file path; keep the built-in Azure Key Vault service example commented out. No credentials or key material belong in the tracked file. Since `.gitignore` currently ignores `keysec.yaml`, update the ignore rules to track this safe default. Users must put sensitive overrides in a separate file selected with `KEYSEC_CONFIG`; edits to the tracked default remain visible to version control.
- **Delegate CLI encryption and decryption to the selected crypto provider.** Add `encrypt` and `decrypt` commands with optional `--provider`; omission uses the configured default crypto provider. Use the positional value when supplied and read standard input when it is omitted. Keep output on stdout and errors on stderr with non-zero status.
- **List configuration metadata without creating providers.** `list-providers` reads the standard KeySec configuration and prints each configured provider's category, name, and implementation type. It does not instantiate providers or print settings, credentials, or secret values. If none are configured, it prints `No providers configured.`
- **List runtime implementations independently.** `list-available-providers` prints the service and crypto implementation types registered with the runtime API. It does not read the KeySec configuration or instantiate providers. Registry APIs must expose registered implementation identifiers for read-only enumeration. If no implementations are registered, it prints `No provider implementations available.`
- **Include examples in help.** The top-level help summarizes all commands and shows a valid example for each; each subcommand's help includes its own usage and example.
- **Print only operation results.** `get-secret` writes the returned value followed by a newline to stdout. `generate-key` writes the created path, never key bytes. `encrypt` and `decrypt` write the provider result followed by a newline. Provider-list commands write only their documented metadata. Errors are written to stderr with non-zero status; expected KeySec and filesystem errors are handled without emitting tracebacks, credentials, or key material.
- **Keep the CLI callable for tests.** A `main(argv=None)`-style entry function can be used by both the console-script entry point and focused tests, with standard streams injectable or redirected in tests.

## Risks / Trade-offs

- [Printing a secret to stdout can expose it if the caller captures terminal output or shell logs] → Make stdout behavior explicit, never include the secret in diagnostics, and document careful handling of redirected output.
- [Positional plaintext may be recorded in shell history or process arguments, and decrypted output is plaintext] → Support stdin as an alternative and document the exposure risk; do not include values in diagnostics.
- [Users may add credentials to the tracked default configuration] → Keep the checked-in file credential-free and direct sensitive configuration to an external `KEYSEC_CONFIG` file.
- [The default key file does not exist until generated] → Document that users must run `keysec generate-key` before encrypting or decrypting with the default configuration; preserve explicit key-file errors.
- [Provider listing could disclose configuration details] → Limit output to provider category, configured name, and implementation type; never serialize settings or instantiate providers.
- [Configured providers and supported implementations could be confused] → Keep separate commands and labels: `list-providers` reads configured entries, while `list-available-providers` reads registered runtime implementation types.
- [A configured provider may have no default key path] → Require `--output` in that case through the provider's existing validation and return its safe error as a non-zero CLI result.
- [No default crypto provider may be configured] → Require an explicit `--provider` in that case and return a clear non-zero CLI error without generating a key.
- [Packaging metadata and CLI behavior can drift] → Test the parser/entry function and verify the installed script target resolves to the same entry point.

## Migration Plan

No existing configuration migration is required. From the repository root, the checked-in `keysec.yaml` is used when `KEYSEC_CONFIG` is unset; users can generate its default local key, then encrypt and decrypt values. Users with sensitive settings should set `KEYSEC_CONFIG` to a separate file. Existing Python API usage remains unchanged.
