"""Tests for KeySec configuration loading."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keysec.config import load_config
from keysec.model.errors import ConfigurationError


class LoadConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.directory = Path(self.temp_dir.name)

    def write_config(self, content: str, name: str = "keysec.yaml") -> Path:
        config_path = self.directory / name
        config_path.write_text(content, encoding="utf-8")
        return config_path

    def test_loads_named_service_and_crypto_providers(self) -> None:
        path = self.write_config(
            """
keysec:
  services:
    default: vault
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
  crypto:
    default: local
    providers:
      local:
        type: aes-gcm
        settings:
          key_file: ./keys/local.key
"""
        )

        config = load_config(path)

        self.assertEqual(config.services.default, "vault")
        self.assertEqual(config.services.select(None).type, "azure-key-vault")
        self.assertEqual(config.services.select("vault").settings["vault_url"],
                         "https://example.vault.azure.net/")
        self.assertEqual(config.crypto.select(None).type, "aes-gcm")
        self.assertEqual(config.crypto.select("local").settings["key_file"],
                         "./keys/local.key")

    def test_reads_path_from_environment(self) -> None:
        path = self.write_config(
            "keysec:\n  services:\n    providers:\n      local:\n        type: test\n"
        )

        with patch.dict(os.environ, {"KEYSEC_CONFIG": str(path)}):
            config = load_config()

        self.assertIn("local", config.services.providers)

    def test_uses_keysec_yaml_in_current_directory_by_default(self) -> None:
        path = self.write_config(
            "keysec:\n  services:\n    providers:\n      local:\n        type: test\n"
        )

        with patch.dict(os.environ):
            os.environ.pop("KEYSEC_CONFIG", None)
            with patch("keysec.config.Path.cwd", return_value=self.directory):
                config = load_config()

        self.assertIn("local", config.services.providers)
        self.assertEqual(path.name, "keysec.yaml")

    def test_rejects_malformed_yaml(self) -> None:
        path = self.write_config("services: [")

        with self.assertRaisesRegex(ConfigurationError, "valid YAML"):
            load_config(path)

    def test_requires_keysec_root_mapping(self) -> None:
        path = self.write_config(
            "services:\n  providers:\n    local:\n      type: test\n"
        )

        with self.assertRaisesRegex(ConfigurationError, "'keysec' must be a YAML mapping"):
            load_config(path)

    def test_rejects_missing_file(self) -> None:
        with self.assertRaisesRegex(ConfigurationError, "does not exist"):
            load_config(self.directory / "missing.yaml")

    def test_rejects_default_that_does_not_name_a_provider(self) -> None:
        path = self.write_config(
            "keysec:\n"
            "  services:\n"
            "    default: missing\n"
            "    providers:\n"
            "      local:\n"
            "        type: test\n"
        )

        with self.assertRaisesRegex(ConfigurationError, "unconfigured provider"):
            load_config(path)

    def test_rejects_non_mapping_provider_settings(self) -> None:
        path = self.write_config(
            "keysec:\n"
            "  crypto:\n"
            "    providers:\n"
            "      local:\n"
            "        type: aes-gcm\n"
            "        settings: invalid\n"
        )

        with self.assertRaisesRegex(ConfigurationError, "settings.*mapping"):
            load_config(path)

    def test_missing_default_is_reported_when_selecting_provider(self) -> None:
        path = self.write_config(
            "keysec:\n  services:\n    providers:\n      local:\n        type: test\n"
        )

        with self.assertRaisesRegex(ConfigurationError, "no default"):
            load_config(path).services.select(None)


if __name__ == "__main__":
    unittest.main()
