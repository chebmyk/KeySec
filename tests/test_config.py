"""Tests for KeySec configuration loading."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from keysec.config import load_config
from keysec.model.errors import ConfigurationError
from keysec.model.provider_config import EnvironmentConfigValue


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
    cipher_prefix: SERVICE_ENC
    providers:
      vault:
        type: azure-key-vault
        settings:
          vault_url: https://example.vault.azure.net/
      custom-prefix:
        type: test
        settings:
          cipher_prefix: CUSTOM_SERVICE
  crypto:
    default: local
    cipher_prefix: CRYPTO_ENC
    providers:
      local:
        type: aes-gcm
        settings:
          key_file: ./keys/local.key
      custom-prefix:
        type: aes-gcm
        settings:
          key_file: ./keys/custom.key
          cipher_prefix: CUSTOM_CRYPTO
"""
        )

        config = load_config(path)

        self.assertEqual(config.services.default, "vault")
        self.assertEqual(config.services.select(None).type, "azure-key-vault")
        self.assertEqual(config.services.select("vault").settings["vault_url"],
                         "https://example.vault.azure.net/")
        self.assertEqual(config.services.cipher_prefix, "SERVICE_ENC")
        self.assertEqual(
            config.services.select("vault").settings["cipher_prefix"],
            "SERVICE_ENC",
        )
        self.assertEqual(
            config.services.select("custom-prefix").settings["cipher_prefix"],
            "CUSTOM_SERVICE",
        )
        self.assertEqual(config.crypto.select(None).type, "aes-gcm")
        self.assertEqual(config.crypto.select("local").settings["key_file"],
                         "./keys/local.key")
        self.assertEqual(config.crypto.cipher_prefix, "CRYPTO_ENC")
        self.assertEqual(
            config.crypto.select("local").settings["cipher_prefix"],
            "CRYPTO_ENC",
        )
        self.assertEqual(
            config.crypto.select("custom-prefix").settings["cipher_prefix"],
            "CUSTOM_CRYPTO",
        )

    def test_cipher_prefixes_default_to_enc(self) -> None:
        path = self.write_config(
            """
keysec:
  services:
    providers:
      vault:
        type: azure-key-vault
  crypto:
    providers:
      local:
        type: aes-gcm
"""
        )

        config = load_config(path)

        self.assertEqual(config.services.cipher_prefix, "ENC")
        self.assertEqual(config.crypto.cipher_prefix, "ENC")
        self.assertEqual(config.services.select("vault").settings["cipher_prefix"], "ENC")
        self.assertEqual(config.crypto.select("local").settings["cipher_prefix"], "ENC")

    def test_rejects_invalid_category_and_provider_cipher_prefixes(self) -> None:
        invalid_configs = (
            "keysec:\n  services:\n    cipher_prefix: ''\n",
            "keysec:\n  crypto:\n    cipher_prefix: 12\n",
            (
                "keysec:\n  services:\n    providers:\n      vault:\n"
                "        type: test\n        settings:\n          cipher_prefix: ''\n"
            ),
            (
                "keysec:\n  crypto:\n    providers:\n      local:\n"
                "        type: test\n        settings:\n          cipher_prefix: 12\n"
            ),
        )
        for content in invalid_configs:
            with self.subTest(content=content):
                path = self.write_config(content)
                with self.assertRaisesRegex(ConfigurationError, "cipher_prefix"):
                    load_config(path)

    def test_expands_environment_variables_in_nested_string_values(self) -> None:
        path = self.write_config(
            """
keysec:
  services:
    providers:
      local:
        type: test
        settings:
          whole: ${WHOLE_VALUE}
          embedded: prefix-${PART_VALUE}-suffix
          nested:
            ${UNCHANGED_KEY}: ${LITERAL_VALUE}
          list:
            - ${WHOLE_VALUE}
            - 42
"""
        )

        with patch.dict(
            os.environ,
            {
                "WHOLE_VALUE": "whole-result",
                "PART_VALUE": "part-result",
                "UNCHANGED_KEY": "changed-key",
                "LITERAL_VALUE": "${WHOLE_VALUE}",
            },
        ):
            settings = load_config(path).services.select("local").settings

        self.assertEqual(settings["whole"], "whole-result")
        self.assertIsInstance(settings["whole"], EnvironmentConfigValue)
        self.assertEqual(settings["embedded"], "prefix-part-result-suffix")
        self.assertEqual(
            settings["nested"],
            {"${UNCHANGED_KEY}": "${WHOLE_VALUE}"},
        )
        self.assertIsInstance(settings["nested"]["${UNCHANGED_KEY}"], EnvironmentConfigValue)
        self.assertEqual(settings["list"], ["whole-result", 42])
        self.assertIsInstance(settings["list"][0], EnvironmentConfigValue)

    def test_rejects_unset_environment_variable_without_exposing_values(self) -> None:
        path = self.write_config(
            "keysec:\n"
            "  services:\n"
            "    providers:\n"
            "      local:\n"
            "        type: test\n"
            "        settings:\n"
            "          value: ${KEYSEC_UNSET_TEST_VALUE}\n"
        )

        with patch.dict(os.environ):
            os.environ.pop("KEYSEC_UNSET_TEST_VALUE", None)
            with self.assertRaisesRegex(
                ConfigurationError,
                "unset environment variable 'KEYSEC_UNSET_TEST_VALUE'",
            ):
                load_config(path)

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
