# Tasks

## 1. AES-GCM Format and Compatibility

- [x] 1.1 Remove the internal `ks1:` prefix from newly encrypted AES-GCM payloads while preserving the configured outer wrapper; verify encrypted output contains only the URL-safe Base64 payload inside the wrapper and round-trips Unicode plaintext.
- [x] 1.2 Remove legacy `ks1:` parsing and reject both wrapped and bare legacy ciphertext, while retaining rejection of malformed and unauthenticated new payloads; verify both old forms fail and current-format round trips/authentication tests pass.

## 2. Documentation

- [x] 2.1 Update README AES-GCM format documentation and encrypted configuration examples to show `<prefix>(<payload>)` and explain that legacy `ks1:` ciphertext is unsupported; verify no new-output example includes the internal `ks1:` marker.

## 3. Integrated Validation

- [x] 3.1 Run focused AES-GCM tests, the full unit test suite, strict OpenSpec validation, and `git diff --check`; verify all checks pass and documented behavior matches the spec.
