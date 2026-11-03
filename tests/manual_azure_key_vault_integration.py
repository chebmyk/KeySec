"""Opt-in live Azure Key Vault connectivity test.

Run explicitly with:
KEYSEC_CONFIG=/path/to/keysec.yaml \
KEYSEC_TEST_SECRET_NAME=connectivity-check \
python -m unittest discover -s tests -p manual_azure_key_vault_integration.py -v
"""

from __future__ import annotations

import os
import unittest

from keysec import KeySec
from keysec.config import load_config


class ManualAzureKeyVaultIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required = ("KEYSEC_CONFIG", "KEYSEC_TEST_SECRET_NAME")
        missing = [name for name in required if not os.environ.get(name)]
        if missing:
            raise RuntimeError(
                "Set the following environment variables to run this manual test: "
                + ", ".join(missing)
            )

        config = load_config(os.environ["KEYSEC_CONFIG"])
        cls.service = config.services.select(None)
        if cls.service.type != "azure-key-vault":
            raise RuntimeError(
                "The configured default service provider must use "
                "'azure-key-vault'."
            )
        cls.secret_name = os.environ["KEYSEC_TEST_SECRET_NAME"]

    def test_retrieves_a_string_secret_from_azure_key_vault(self) -> None:
        value = KeySec().get_secret(self.secret_name, provider=self.service.name)
        if not isinstance(value, str):
            self.fail("Azure Key Vault did not return a string secret value.")


if __name__ == "__main__":
    unittest.main()
