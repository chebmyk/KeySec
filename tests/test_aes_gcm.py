"""Tests for AES-GCM ciphertext format and authentication."""

from __future__ import annotations

import base64
import stat
import tempfile
import unittest
from pathlib import Path

from keysec.model.errors import ConfigurationError, CryptoError
from keysec.providers.crypto.aes_gcm import AESGCMProvider


class AESGCMProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.key_file = Path(self.temp_dir.name) / "key.bin"
        self.key_file.write_bytes(bytes(range(32)))
        self.provider = AESGCMProvider("local", {"key_file": str(self.key_file)})

    def test_round_trips_unicode_text_without_internal_version_prefix(self) -> None:
        ciphertext = self.provider.encrypt("Hello, world")

        self.assertTrue(ciphertext.startswith("ENC("))
        payload = self.provider.unwrap_ciphertext(ciphertext)
        decoded = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        self.assertGreaterEqual(len(decoded), 12 + 16)
        self.assertEqual(self.provider.decrypt(ciphertext), "Hello, world")

    def test_round_trips_with_provider_prefix_override(self) -> None:
        provider = AESGCMProvider(
            "custom",
            {"key_file": str(self.key_file), "cipher_prefix": "SEALED"},
        )
        ciphertext = provider.encrypt("custom prefix")

        self.assertTrue(ciphertext.startswith("SEALED("))
        self.assertEqual(provider.decrypt(ciphertext), "custom prefix")

    def test_rejects_invalid_cipher_prefix_configuration(self) -> None:
        for prefix in ("", 42, None):
            with self.subTest(prefix=prefix):
                with self.assertRaisesRegex(ConfigurationError, "cipher_prefix"):
                    AESGCMProvider(
                        "invalid",
                        {"key_file": str(self.key_file), "cipher_prefix": prefix},
                    )

    def test_uses_a_fresh_nonce_for_each_encryption(self) -> None:
        first = self.provider.encrypt("same text")
        second = self.provider.encrypt("same text")

        self.assertNotEqual(first, second)
        self.assertEqual(self.provider.decrypt(first), "same text")
        self.assertEqual(self.provider.decrypt(second), "same text")

    def test_rejects_modified_ciphertext_without_returning_plaintext(self) -> None:
        ciphertext = self.provider.encrypt("do not disclose")
        encoded = self.provider.unwrap_ciphertext(ciphertext)
        payload = bytearray(
            base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        )
        payload[-1] ^= 1
        modified = self.provider.wrap_ciphertext(
            base64.urlsafe_b64encode(payload).rstrip(b"=").decode()
        )

        with self.assertRaisesRegex(CryptoError, "authentication failed") as raised:
            self.provider.decrypt(modified)

        self.assertNotIn("do not disclose", str(raised.exception))

    def test_rejects_malformed_ciphertext(self) -> None:
        for ciphertext in (
            "not-a-ciphertext",
            "***",
            "abc",
            "ENC(***",
            "ENC(***))extra",
            "ENC(***",
        ):
            with self.subTest(ciphertext=ciphertext):
                with self.assertRaises(CryptoError):
                    self.provider.decrypt(ciphertext)

    def test_rejects_unknown_ciphertext_version(self) -> None:
        with self.assertRaisesRegex(CryptoError, "unsupported"):
            self.provider.decrypt("ENC(ks2:AA)")

    def test_generates_binary_key_at_provider_path_with_restrictive_permissions(self) -> None:
        configured_path = Path(self.temp_dir.name) / "generated.key"
        provider = AESGCMProvider("local", {"key_file": str(configured_path)})
        generated_path = Path(provider.generate_key())

        self.assertEqual(generated_path, configured_path)
        self.assertEqual(len(generated_path.read_bytes()), 32)
        self.assertEqual(stat.S_IMODE(generated_path.stat().st_mode), 0o600)

    def test_generates_key_at_explicit_path_and_does_not_overwrite(self) -> None:
        output_path = Path(self.temp_dir.name) / "explicit.key"
        returned_path = self.provider.generate_key(output_path)
        generated_key = output_path.read_bytes()

        self.assertEqual(returned_path, str(output_path))
        self.assertEqual(len(generated_key), 32)
        with self.assertRaises(FileExistsError):
            self.provider.generate_key(output_path)
        self.assertEqual(output_path.read_bytes(), generated_key)

    def test_generated_key_can_encrypt_and_decrypt(self) -> None:
        output_path = Path(self.temp_dir.name) / "roundtrip.key"
        self.provider.generate_key(output_path)
        provider = AESGCMProvider("generated", {"key_file": str(output_path)})

        self.assertEqual(provider.decrypt(provider.encrypt("key check")), "key check")

    def test_reports_key_file_path_errors(self) -> None:
        missing_parent_path = Path(self.temp_dir.name) / "missing" / "key.bin"

        with self.assertRaisesRegex(CryptoError, "Unable to create"):
            self.provider.generate_key(missing_parent_path)

    def test_requires_output_path_when_provider_has_no_key_file_setting(self) -> None:
        provider = AESGCMProvider("unconfigured", {})

        with self.assertRaisesRegex(CryptoError, "No key file path"):
            provider.generate_key()

    def test_explicit_key_file_overrides_provider_setting(self) -> None:
        override_path = Path(self.temp_dir.name) / "override.key"
        override_path.write_bytes(bytes(reversed(range(32))))
        ciphertext = self.provider.encrypt("override", override_path)

        self.assertEqual(self.provider.decrypt(ciphertext, override_path), "override")
        with self.assertRaises(CryptoError):
            self.provider.decrypt(ciphertext)


if __name__ == "__main__":
    unittest.main()
