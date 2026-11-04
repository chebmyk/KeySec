"""Tests for the KeySec command-line interface."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch

from keysec.cli import main
from keysec.model.errors import ConfigurationError, SecretRetrievalError


class KeySecCLITests(unittest.TestCase):
    def run_cli(self, args: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(args)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_get_secret_uses_default_service_provider(self) -> None:
        keysec = MagicMock()
        keysec.get_secret.return_value = "secret-value"
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(["get-secret", "database-password"])

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "secret-value\n")
        self.assertEqual(stderr, "")
        keysec.get_secret.assert_called_once_with("database-password", provider=None)

    def test_get_secret_selects_named_service_provider(self) -> None:
        keysec = MagicMock()
        keysec.get_secret.return_value = "secret-value"
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, _ = self.run_cli(
                ["get-secret", "database-password", "--provider", "vault"]
            )

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "secret-value\n")
        keysec.get_secret.assert_called_once_with(
            "database-password",
            provider="vault",
        )

    def test_get_secret_reports_failure_to_stderr_without_printing_secret(self) -> None:
        keysec = MagicMock()
        keysec.get_secret.side_effect = SecretRetrievalError("lookup failed")
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(["get-secret", "missing"])

        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("lookup failed", stderr)

    def test_generate_key_uses_provider_configured_path(self) -> None:
        provider = MagicMock()
        provider.generate_key.return_value = "/keys/generated.key"
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(
                ["generate-key", "--provider", "local"]
            )

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "/keys/generated.key\n")
        self.assertEqual(stderr, "")
        keysec.get_provider.assert_called_once_with("local", provider_type="crypto")
        provider.generate_key.assert_called_once_with(None)

    def test_generate_key_accepts_explicit_path(self) -> None:
        provider = MagicMock()
        provider.generate_key.return_value = "/tmp/key.bin"
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(
                ["generate-key", "--provider", "local", "--output", "/tmp/key.bin"]
            )

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "/tmp/key.bin\n")
        self.assertEqual(stderr, "")
        provider.generate_key.assert_called_once_with("/tmp/key.bin")

    def test_generate_key_reports_existing_path_error_without_key_material(self) -> None:
        provider = MagicMock()
        provider.generate_key.side_effect = FileExistsError("/tmp/existing.key")
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(
                ["generate-key", "--provider", "local"]
            )

        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("existing.key", stderr)
        self.assertNotIn("key material", stderr)

    def test_generate_key_reports_provider_error_without_key_material(self) -> None:
        provider = MagicMock()
        provider.generate_key.side_effect = ConfigurationError("No key file path")
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(
                ["generate-key", "--provider", "local"]
            )

        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("No key file path", stderr)
        self.assertNotIn("key material", stderr)


if __name__ == "__main__":
    unittest.main()
