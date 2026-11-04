# Design

## Context

AES-GCM currently prepends `ks1:` to the URL-safe Base64 encoding of the nonce and authenticated ciphertext, then wraps that string with the configured provider prefix. The cryptography requirement currently calls the encoded payload versioned. See the proposal and spec delta for the format change and compatibility contract.

## Goals / Non-Goals

**Goals:**
- Emit newly encrypted AES-GCM ciphertext as the configured wrapper around the encoded cryptographic payload, without an internal textual version marker.
- Reject existing wrapped and bare `ks1:` values rather than maintaining a legacy compatibility path.
- Keep authentication, nonce generation, key handling, and error behavior unchanged.

**Non-Goals:**
- Change the AES-GCM algorithm, key size, nonce length, tag handling, or key-file behavior.
- Change the AES-GCM payload layout beyond removing the internal textual marker.
- Change the generic crypto-provider wrapper contract or configuration.

## Decisions

- **Use the configured wrapper as the new output label.** Encode the nonce followed by AES-GCM ciphertext and its authentication tag as URL-safe Base64, then place that payload directly inside the configured wrapper. This removes redundant format text while retaining the existing cryptographic payload bytes. Keeping `ks1:` in new output was considered but would preserve the duplication the change addresses.
- **Decode only the new Base64 payload.** After removing a matching configured wrapper, decode the entire inner value as URL-safe Base64. Do not strip or recognize `ks1:` as a legacy marker; its colon makes it invalid Base64 and the provider rejects it as malformed. This keeps the decryption path simple and ensures obsolete wrapped and bare forms are not accepted.
- **Test rejection of old ciphertext.** Use known `ks1:` wrapped and bare examples and verify both fail with a safe format error. Continue testing authentication failures using the new unversioned payload format.
- **Document the breaking compatibility decision.** Update the README's AES-GCM description and encrypted configuration examples to show the wrapper around the Base64 payload without `ks1:`. State that legacy ciphertext is not supported and must be replaced with a value generated in the new format.

## Risks / Trade-offs

- [Existing stored ciphertext using `ks1:` will no longer decrypt] → Mark this as a breaking format change and require affected values to be regenerated in the new format.
- [Without a version marker, future payload changes need another distinction] → Keep this change limited to the currently specified nonce/ciphertext/tag layout; require a separately designed format change before changing payload interpretation.

## Migration Plan

New encryption outputs use `<prefix>(<payload>)`, and the reader accepts only this unversioned Base64 payload format. Existing wrapped and bare `ks1:` ciphertexts must be replaced by values encrypted with the new format before upgrading. Callers that inspect or parse the internal `ks1:` text must stop expecting it. Rolling back the reader alone would not accept ciphertext written in the new output format, so consumers should be upgraded before exchanging new ciphertext across versions.
