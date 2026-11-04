# Proposal

## Why

The repository currently defines a Python package and `keysec` console entry point, but has no repeatable packaging scripts. Platform-specific scripts will let CI and maintainers build a standalone CLI executable or distributable wheel using the existing project metadata.

## What Changes

- Add a dedicated `.ci/` directory with executable build scripts for Windows (`.cmd`), Unix/Linux (`.sh`), and macOS ARM64 (`.sh`).
- Provide one PyInstaller single-file executable build script and one wheel build script for each platform target.
- Have each script resolve and run from the repository root, use the existing `pyproject.toml` package metadata and `keysec` entry point, and report failures with a non-zero exit status.
- Document the script names, prerequisites, invocation, and output locations in the README.
- Keep builds native-host only; cross-compilation and hosted CI workflow configuration are out of scope.

## Capabilities

### New Capabilities

None. This change adds repository build tooling and does not change application behavior.

### Modified Capabilities

None.

## Impact

The `.ci/` directory, README packaging instructions, packaging/build dependencies used by the scripts, and generated artifacts under `dist/`. No application API changes are expected.
