# Design

## Context

The package uses setuptools with a `src/` layout and declares the `keysec` console entry point in `pyproject.toml`. There is no existing CI script directory or build automation. See proposal.md for motivation and scope.

## Goals / Non-Goals

**Goals:**
- Keep packaging commands reproducible in intent and independent of the caller's current directory.
- Produce a one-file CLI executable with PyInstaller and a wheel from the existing package metadata.
- Fail early when a platform-specific script is launched on an unsupported host or architecture.

**Non-Goals:**
- Cross-compiling executables or wheels for a different operating system or architecture.
- Creating hosted CI workflow definitions or changing runtime application behavior.

## Decisions

- Place six entry-point scripts in `.ci/`, one executable and one wheel builder per target: Windows (`.cmd`), Unix/Linux (`.sh`), and macOS ARM64 (`.sh`). Separate scripts make platform selection explicit and provide directly runnable commands for local use and CI runners.
- Resolve the repository root relative to each script, so invocation works from any current directory.
- Use a local isolated virtual environment for build tooling rather than installing PyInstaller or the wheel builder into the caller's Python environment. Install the project and PyInstaller in the executable build environment; use `python -m build --wheel` for wheel generation.
- Build the installed `keysec` CLI as a PyInstaller one-file executable named `keysec` (or `keysec.exe` on Windows). Build the wheel with the existing `pyproject.toml`; do not force platform tags when the current source package is pure Python.
- Validate the macOS ARM64 script is running under Apple Silicon (`Darwin` and `arm64`) and validate the Unix/Linux script is running on its supported host. The scripts build for the host Python/runtime and do not attempt cross-compilation.
- Require the Linux executable host to provide `objdump` from `binutils`, and report a clear prerequisite error before installing Python build dependencies when it is missing.
- Write build outputs to the repository's `dist/` directory, which is already ignored by `.gitignore`; document the commands and generated artifacts in the README.

Alternatives considered: a single parameterized script would reduce duplication but make platform-specific invocation and Windows error handling less transparent; relying on globally installed tools would be shorter but less isolated and less predictable.

## Risks / Trade-offs

- [First run requires network access to install build tools and package dependencies] → Use normal pip error propagation and document the prerequisites; do not hide installation failures.
- [Linux PyInstaller requires system-level `objdump`] → Check for it before preparing the build environment and document `binutils` as a host prerequisite.
- [PyInstaller output can vary across Python and PyInstaller versions] → Build with the native platform's Python and leave tool versions visible in the script or its output for diagnosis.
- [A wheel built on each platform may be byte-equivalent or share the same universal wheel tag] → Treat each platform script as a host-specific build entry point, not a promise of different wheel binaries.

## Migration Plan

No migration is required. Run the desired script from any directory; generated files are placed in `dist/`. Removing generated output requires only deleting the specific build artifacts.
