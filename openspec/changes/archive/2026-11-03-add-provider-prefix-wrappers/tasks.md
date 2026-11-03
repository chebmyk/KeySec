# Tasks

## 1. Service Secret References

- [x] 1.1 Add `secret_prefix` validation/default handling and unwrap matching references in `KeySec.get_secret`; verify `KEY(secret_id)`, a custom prefix, unwrapped names, and invalid settings in focused API/configuration tests.
- [x] 1.2 Document the default `KEY` wrapper and per-provider `secret_prefix` override in the README; verify the YAML and `get_secret` examples match the implemented format.

## 2. Crypto Ciphertext Wrappers

- [x] 2.1 Add the default `ENC` prefix and `cipher_prefix` override to the crypto-provider contract, and wrap/unwrap AES-GCM ciphertext while retaining bare `ks1:` decryption; verify default, override, malformed input, and legacy behavior in focused crypto tests.
- [x] 2.2 Update custom-provider extension guidance and AES-GCM documentation with the wrapped format and compatibility notes; verify examples match the provider contract.

## 3. Integration Verification

- [x] 3.1 Add or update an end-to-end configuration/API test covering service and crypto prefix overrides together; verify provider selection still uses the selected provider's configured prefix.
- [x] 3.2 Run the complete automated test suite and OpenSpec validation; verify all tests pass and the change validates without errors.

## 4. Encrypted Provider Configuration

- [x] 4.1 Add category-level `cipher_prefix` settings for crypto and service groups, defaulting to `ENC`, with per-provider overrides; verify category defaults, overrides, and invalid values in configuration tests.
- [x] 4.2 Decrypt matching wrapped string values in provider settings through the configured default crypto provider while leaving prefix controls and its bootstrap settings plaintext; verify unwrapped passthrough, crypto/service resolution, and explicit failure cases in focused tests.

## 5. Encrypted Service Credentials

- [x] 5.1 Allow Azure `client_secret` to use either its existing environment-variable name or a wrapped encrypted literal that is decrypted and passed directly to authentication; verify both modes, no environment fallback on decryption failure, and document the configuration and key-file setup in the README.
- [x] 5.2 Add end-to-end tests for category prefixes, provider overrides, and encrypted Azure credentials; verify the selected default crypto provider decrypts values and existing `KEY(...)` secret references remain unchanged.
- [x] 5.3 Run the complete automated test suite and strict OpenSpec validation; verify all tests pass and the revised change validates without errors.
