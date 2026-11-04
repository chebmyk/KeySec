# Tasks

## 1. Wheel Build Scripts

- [x] 1.1 Add Windows, Unix/Linux, and macOS ARM64 wheel build scripts under `.ci/`; verify the wheel output is created from the repository root and the macOS ARM64 script rejects non-ARM64 hosts.
- [x] 1.2 Document wheel build prerequisites, commands, and `dist/` output in the README; verify the documented commands match the scripts and produce a wheel on each native target.

## 2. Standalone Executable Scripts

- [x] 2.1 Add Windows, Unix/Linux, and macOS ARM64 PyInstaller one-file executable scripts under `.ci/`; verify each produces the platform-native `keysec` executable and that the macOS ARM64 script rejects non-ARM64 hosts.
- [x] 2.2 Document executable build commands and output locations in the README; verify the generated executable runs `--help` on each native target.

## 3. Packaging Integration

- [ ] 3.1 Verify all six scripts can be invoked from outside the repository root, fail with a non-zero status on build errors, and leave generated artifacts under the ignored `dist/` directory.
