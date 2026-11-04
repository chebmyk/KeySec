# Tasks

## 1. CLI Commands and Packaging

- [x] 1.1 Implement the `keysec get-secret` and `keysec generate-key` command handlers using the existing `KeySec` facade and crypto-provider API; verify focused CLI tests cover defaults, provider selection, explicit output paths, stdout results, stderr failures, and non-zero statuses without exposing key material.
- [x] 1.2 Register the installed `keysec` console script in `pyproject.toml`; verify package metadata resolves the script to the CLI entry function and the command exposes its help interface.
- [x] 1.3 Document command syntax, `KEYSEC_CONFIG` usage, examples, stdout secret-handling caution, and generated-key path output in `README.md`; verify examples match CLI help and supported arguments.
- [ ] 1.4 Add `keysec list-providers` to list configured service and crypto provider categories, names, and types without instantiating providers or exposing settings; test populated and empty configuration output.
- [ ] 1.5 Add `keysec list-available-providers` to list registered service and crypto implementation types without requiring configuration; expose read-only implementation identifiers from the registries and test populated and empty registries.
- [ ] 1.6 Make `generate-key --provider` optional, selecting the configured default crypto provider when omitted; test default selection, named override, and a clear error when no default is configured.
- [ ] 1.7 Add clear valid examples to top-level and each subcommand's `--help` output, including default and named-provider key generation and both provider-list commands; test that examples cover all supported operations.
- [ ] 1.8 Update the README with both provider-list commands and examples for all commands, including default and named-provider key generation, retaining the secret-output caution and generated-key path behavior.

## 2. Integrated Validation

- [ ] 2.1 Run the full unit test suite, strict OpenSpec change validation, and `git diff --check`; verify all tests and validation pass and the command is ready for package installation.
