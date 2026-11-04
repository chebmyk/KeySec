"""Tests for the checked-in default configuration."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import patch

from keysec.config import load_config

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class DefaultConfigTests(unittest.TestCase):
    def test_default_configuration_loads_with_only_local_crypto(self) -> None:
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("keysec.config.Path.cwd", return_value=REPOSITORY_ROOT),
        ):
            config = load_config()

        self.assertIsNone(config.services.default)
        self.assertEqual(config.services.providers, {})
        self.assertEqual(config.crypto.default, "local")
        self.assertEqual(config.crypto.select(None).type, "aes-gcm")
        self.assertEqual(
            config.crypto.select(None).settings["key_file"],
            "./keysec.key",
        )

    def test_default_configuration_contains_no_credentials_or_key_material(self) -> None:
        contents = (REPOSITORY_ROOT / "keysec.yaml").read_text(encoding="utf-8")
        active_lines = [
            line for line in contents.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]

        self.assertNotRegex(
            "\n".join(active_lines),
            r"(?i)\b(client_secret|password|credential|private_key|key_material)\s*:",
        )
        self.assertIn("# services:", contents)
        self.assertIn("#   default: vault", contents)


if __name__ == "__main__":
    unittest.main()
