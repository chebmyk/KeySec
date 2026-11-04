# Tasks

## 1. CLI Commands and Packaging

- [x] 1.1 Implement the `keysec get-secret` and `keysec generate-key` command handlers using the existing `KeySec` facade and crypto-provider API; verify focused CLI tests cover defaults, provider selection, explicit output paths, stdout results, stderr failures, and non-zero statuses without exposing key material.
- [x] 1.2 Register the installed `keysec` console script in `pyproject.toml`; verify package metadata resolves the script to the CLI entry function and the command exposes its help interface.
- [x] 1.3 Document command syntax, `KEYSEC_CONFIG` usage, examples, stdout secret-handling caution, and generated-key path output in `README.md`; verify examples match CLI help and supported arguments.
- [x] 1.4 Add a tracked root `keysec.yaml` with only the default local AES-GCM provider active, a local key-file path, and commented examples for supported alternatives; adjust `.gitignore` and test default loading and credential-free contents.
- [x] 1.5 Make `generate-key --provider` optional, selecting the configured default crypto provider when omitted; test default selection, named override, and a clear error when no default is configured.
- [x] 1.6 Add `encrypt` and `decrypt` commands using the default or a named crypto provider and accepting either positional input or standard input; test round trips, both input modes, provider selection, and error output.
- [x] 1.7 Add `keysec list-providers` to list configured service and crypto provider categories, names, and types without instantiating providers or exposing settings; test populated and empty configuration output.
- [x] 1.8 Add `keysec list-available-providers` to list registered service and crypto implementation types without requiring configuration; expose read-only implementation identifiers from the registries and test populated and empty registries.
- [x] 1.9 Add clear valid examples to top-level and each subcommand's `--help` output, including default and named-provider key generation, encryption/decryption, and both provider-list commands; test that examples cover all supported operations.
- [x] 1.10 Update the README with the default configuration, key-generation prerequisite, all command examples and input modes, and cautions for positional values and plaintext output; verify documented invocations match CLI behavior.

## 2. Integrated Validation

- [x] 2.1 Run the full unit test suite, strict OpenSpec change validation, and `git diff --check`; verify all tests and validation pass and the command is ready for package installation.
