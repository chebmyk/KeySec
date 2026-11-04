# Proposal

## Why

AES-GCM ciphertext currently includes an internal `ks1:` prefix inside the configured outer wrapper, duplicating format labeling and making wrapped values unnecessarily verbose. Use the configured wrapper directly around the encoded cryptographic payload, without retaining support for the obsolete `ks1:` format.

## What Changes

- **BREAKING**: Change new AES-GCM output from `<prefix>(ks1:<payload>)` to `<prefix>(<payload>)`, where the URL-safe Base64 payload contains the nonce and authenticated ciphertext/tag.
- Do not support decryption of legacy wrapped or bare `ks1:` ciphertexts.
- Update the cryptography requirement, AES-GCM tests, and README examples and format documentation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cryptography`: Specify the new unversioned payload for encryption and decryption and reject legacy `ks1:` ciphertext.

## Impact

- AES-GCM encryption/decryption format handling and focused tests.
- Cryptography capability specification and README ciphertext examples.
- No new dependency or public API method is required.
