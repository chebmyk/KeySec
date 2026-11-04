"""Tests for the KeySec command-line interface."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch

from keysec.cli import main
from keysec.model.errors import ConfigurationError, SecretRetrievalError


class KeySecCLITests(unittest.TestCase):
    def run_cli(
        self,
        args: list[str],
        stdin: str | None = "",
    ) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            if stdin is None:
                status = main(args)
            else:
                with patch("keysec.cli.sys.stdin", io.StringIO(stdin)):
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

    def test_generate_key_uses_default_crypto_provider(self) -> None:
        provider = MagicMock()
        provider.generate_key.return_value = "/keys/default.key"
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(["generate-key"])

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "/keys/default.key\n")
        self.assertEqual(stderr, "")
        keysec.get_provider.assert_called_once_with(None, provider_type="crypto")

    def test_generate_key_without_default_reports_configuration_error(self) -> None:
        keysec = MagicMock()
        keysec.get_provider.side_effect = ConfigurationError(
            "No provider was selected and no default is configured"
        )
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(["generate-key"])

        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("no default is configured", stderr)

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

    def test_encrypt_and_decrypt_use_positional_values_and_named_provider(self) -> None:
        provider = MagicMock()
        provider.encrypt.return_value = "ENC(ciphertext)"
        provider.decrypt.return_value = "plaintext"
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            encrypt_status, encrypt_stdout, _ = self.run_cli(
                ["encrypt", "plaintext", "--provider", "backup"]
            )
            decrypt_status, decrypt_stdout, _ = self.run_cli(
                ["decrypt", "ENC(ciphertext)", "--provider", "backup"]
            )

        self.assertEqual((encrypt_status, decrypt_status), (0, 0))
        self.assertEqual(encrypt_stdout, "ENC(ciphertext)\n")
        self.assertEqual(decrypt_stdout, "plaintext\n")
        self.assertEqual(
            keysec.get_provider.call_args_list,
            [
                call("backup", provider_type="crypto"),
                call("backup", provider_type="crypto"),
            ],
        )
        provider.encrypt.assert_called_once_with("plaintext")
        provider.decrypt.assert_called_once_with("ENC(ciphertext)")

    def test_encrypt_and_decrypt_read_standard_input_when_value_is_omitted(self) -> None:
        provider = MagicMock()
        provider.encrypt.return_value = "ENC(from-stdin)"
        provider.decrypt.return_value = "decrypted-stdin"
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            encrypt_status, encrypt_stdout, _ = self.run_cli(
                ["encrypt"], stdin="from-stdin"
            )
            decrypt_status, decrypt_stdout, _ = self.run_cli(
                ["decrypt"], stdin="ENC(to-decrypt)"
            )

        self.assertEqual((encrypt_status, decrypt_status), (0, 0))
        self.assertEqual(encrypt_stdout, "ENC(from-stdin)\n")
        self.assertEqual(decrypt_stdout, "decrypted-stdin\n")
        provider.encrypt.assert_called_once_with("from-stdin")
        provider.decrypt.assert_called_once_with("ENC(to-decrypt)")

    def test_crypto_commands_prefer_positional_value_to_stdin(self) -> None:
        provider = MagicMock()
        provider.encrypt.return_value = "ENC(positional)"
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        stdin = io.StringIO("ignored stdin")
        with (
            patch("keysec.cli.KeySec", return_value=keysec),
            patch("keysec.cli.sys.stdin", stdin),
        ):
            status, stdout, _ = self.run_cli(["encrypt", "positional"], stdin=None)

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "ENC(positional)\n")
        self.assertEqual(stdin.tell(), 0)
        provider.encrypt.assert_called_once_with("positional")

    def test_encrypt_and_decrypt_report_errors_without_output(self) -> None:
        provider = MagicMock()
        provider.encrypt.side_effect = ValueError("encryption failed")
        keysec = MagicMock()
        keysec.get_provider.return_value = provider
        with patch("keysec.cli.KeySec", return_value=keysec):
            status, stdout, stderr = self.run_cli(["encrypt", "secret"])

        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        self.assertIn("encryption failed", stderr)

    def test_default_crypto_configuration_round_trips_with_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "keysec.yaml"
            key_path = Path(temp_dir) / "local.key"
            config_path.write_text(
                "keysec:\n"
                "  crypto:\n"
                "    default: local\n"
                "    providers:\n"
                "      local:\n"
                "        type: aes-gcm\n"
                f'        settings:\n          key_file: "{key_path}"\n',
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"KEYSEC_CONFIG": str(config_path)}):
                generate_status, generated_path, _ = self.run_cli(["generate-key"])
                encrypt_status, ciphertext, _ = self.run_cli(
                    ["encrypt", "round trip"]
                )
                decrypt_status, plaintext, stderr = self.run_cli(
                    ["decrypt", ciphertext.strip()]
                )
                self.assertEqual(
                    (generate_status, encrypt_status, decrypt_status),
                    (0, 0, 0),
                )
                self.assertEqual(generated_path, f"{key_path}\n")
                self.assertTrue(key_path.is_file())

        self.assertEqual(plaintext, "round trip\n")
        self.assertEqual(stderr, "")

    def test_audit_logging_records_cli_crypto_outcomes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            directory = Path(temp_dir)
            audit_path = directory / "audit.log"
            key_path = directory / "local.key"
            config_path = directory / "keysec.yaml"
            config_path.write_text(
                "keysec:\n"
                "  audit_logging:\n"
                "    enabled: true\n"
                f"    file: {audit_path}\n"
                "  crypto:\n"
                "    default: local\n"
                "    providers:\n"
                "      local:\n"
                "        type: aes-gcm\n"
                "        settings:\n"
                f"          key_file: {key_path}\n",
                encoding="utf-8",
            )
            plaintext = "AUDIT_CLI_PLAINTEXT_MARKER"
            with patch.dict(os.environ, {"KEYSEC_CONFIG": str(config_path)}):
                generate_status, _, _ = self.run_cli(["generate-key"])
                encrypt_status, ciphertext, _ = self.run_cli(
                    ["encrypt", plaintext]
                )
                decrypt_status, decrypted, _ = self.run_cli(
                    ["decrypt", ciphertext.strip()]
                )
                failure_status, _, failure_stderr = self.run_cli(
                    ["decrypt", "invalid-ciphertext"]
                )

            self.assertEqual(
                (generate_status, encrypt_status, decrypt_status, failure_status),
                (0, 0, 0, 1),
            )
            self.assertEqual(decrypted, f"{plaintext}\n")
            self.assertNotEqual(failure_stderr, "")
            contents = audit_path.read_text(encoding="utf-8")
            self.assertNotIn(plaintext, contents)
            self.assertNotIn(ciphertext.strip(), contents)
            entries = [json.loads(line) for line in contents.splitlines()]
            self.assertEqual(
                [(entry["operation"], entry["outcome"]) for entry in entries],
                [
                    ("key_generation", "success"),
                    ("encrypt", "success"),
                    ("decrypt", "success"),
                    ("decrypt", "failure"),
                ],
            )
            self.assertTrue(all(entry["provider"] == "local" for entry in entries))

    def test_list_providers_shows_only_provider_metadata(self) -> None:
        config = SimpleNamespace(
            services=SimpleNamespace(
                providers={
                    "vault": SimpleNamespace(
                        type="azure-key-vault",
                        settings={"client_secret": "must-not-print"},
                    )
                }
            ),
            crypto=SimpleNamespace(
                providers={
                    "local": SimpleNamespace(
                        type="aes-gcm",
                        settings={"key_file": "/secret/path"},
                    )
                }
            ),
        )
        with (
            patch("keysec.cli.load_config", return_value=config),
            patch("keysec.cli.KeySec") as keysec_constructor,
        ):
            status, stdout, stderr = self.run_cli(["list-providers"])

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "service: vault (azure-key-vault)\ncrypto: local (aes-gcm)\n",
        )
        self.assertEqual(stderr, "")
        keysec_constructor.assert_not_called()
        self.assertNotIn("must-not-print", stdout)
        self.assertNotIn("/secret/path", stdout)

    def test_list_providers_reports_empty_configuration(self) -> None:
        config = SimpleNamespace(
            services=SimpleNamespace(providers={}),
            crypto=SimpleNamespace(providers={}),
        )
        with patch("keysec.cli.load_config", return_value=config):
            status, stdout, stderr = self.run_cli(["list-providers"])

        self.assertEqual(status, 0)
        self.assertEqual(stdout, "No providers configured.\n")
        self.assertEqual(stderr, "")

    def test_list_available_providers_does_not_load_configuration(self) -> None:
        service_registry = SimpleNamespace(
            implementation_types=("azure-key-vault",)
        )
        crypto_registry = SimpleNamespace(implementation_types=("aes-gcm",))
        with (
            patch("keysec.cli.service_provider_registry", service_registry),
            patch("keysec.cli.crypto_provider_registry", crypto_registry),
            patch("keysec.cli.load_config") as load_config,
            patch("keysec.cli.KeySec") as keysec_constructor,
        ):
            status, stdout, stderr = self.run_cli(["list-available-providers"])

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "service: azure-key-vault\ncrypto: aes-gcm\n",
        )
        self.assertEqual(stderr, "")
        load_config.assert_not_called()
        keysec_constructor.assert_not_called()

    def test_list_available_providers_reports_empty_registries(self) -> None:
        empty_registry = SimpleNamespace(implementation_types=())
        with (
            patch("keysec.cli.service_provider_registry", empty_registry),
            patch("keysec.cli.crypto_provider_registry", empty_registry),
        ):
            status, stdout, stderr = self.run_cli(["list-available-providers"])

        self.assertEqual(status, 0)
        self.assertEqual(
            stdout,
            "No provider implementations available.\n",
        )
        self.assertEqual(stderr, "")

    def test_help_shows_examples_for_each_command(self) -> None:
        commands = (
            "get-secret",
            "generate-key",
            "encrypt",
            "decrypt",
            "list-providers",
            "list-available-providers",
        )
        stdout = io.StringIO()
        with redirect_stdout(stdout), self.assertRaises(SystemExit) as exit_info:
            main(["--help"])

        self.assertEqual(exit_info.exception.code, 0)
        for command in commands:
            self.assertIn(f"keysec {command}", stdout.getvalue())
        self.assertIn(
            "keysec generate-key --provider backup --output ./backup.key",
            stdout.getvalue(),
        )

        for command in commands:
            command_stdout = io.StringIO()
            with (
                redirect_stdout(command_stdout),
                self.assertRaises(SystemExit) as command_exit,
            ):
                main([command, "--help"])
            self.assertEqual(command_exit.exception.code, 0)
            self.assertIn(f"keysec {command}", command_stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
