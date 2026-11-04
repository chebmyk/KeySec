"""Command-line interface for KeySec."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from keysec import KeySec
from keysec.config import load_config
from keysec.model.errors import KeySecError
from keysec.providers.crypto.crypto_provider_registry import crypto_provider_registry
from keysec.providers.service.service_provider_registry import service_provider_registry


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="keysec",
        description="Retrieve secrets and perform text cryptography with KeySec.",
        epilog=(
            "Examples:\n"
            "  keysec get-secret database-password\n"
            "  keysec generate-key\n"
            "  keysec generate-key --provider backup --output ./backup.key\n"
            "  keysec list-providers\n"
            "  keysec list-available-providers\n"
            "  keysec encrypt 'sensitive text'\n"
            "  printf %s 'sensitive text' | keysec encrypt\n"
            "  keysec decrypt 'ENC(ciphertext)'"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    get_secret = commands.add_parser(
        "get-secret",
        help="retrieve a secret using a configured service provider",
        description="Retrieve a secret using the configured default or a named service provider.",
        epilog="Example: keysec get-secret database-password",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    get_secret.add_argument("secret", help="secret name or wrapped secret reference")
    get_secret.add_argument(
        "--provider",
        help="configured service provider name (defaults to keysec.services.default)",
    )

    generate_key = commands.add_parser(
        "generate-key",
        help="generate a key using a configured crypto provider",
        description="Generate a key using the configured default or a named crypto provider.",
        epilog=(
            "Examples:\n"
            "  keysec generate-key\n"
            "  keysec generate-key --provider backup --output ./backup.key"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    generate_key.add_argument(
        "--provider",
        help="configured crypto provider name (defaults to keysec.crypto.default)",
    )
    generate_key.add_argument(
        "--output",
        help="key file path (defaults to the provider's configured key_file)",
    )

    for operation, description, example in (
        (
            "encrypt",
            "encrypt text using a configured crypto provider",
            "keysec encrypt 'sensitive text'",
        ),
        (
            "decrypt",
            "decrypt text using a configured crypto provider",
            "keysec decrypt 'ENC(ciphertext)'",
        ),
    ):
        command = commands.add_parser(
            operation,
            help=description,
            description=f"{description.capitalize()}; omit VALUE to read from standard input.",
            epilog=f"Example: {example}",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        command.add_argument(
            "value",
            nargs="?",
            help="value to process (read from standard input when omitted)",
        )
        command.add_argument(
            "--provider",
            help="configured crypto provider name (defaults to keysec.crypto.default)",
        )

    commands.add_parser(
        "list-providers",
        help="list providers configured in the KeySec YAML file",
        description="List configured providers without showing their settings.",
        epilog="Example: keysec list-providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    commands.add_parser(
        "list-available-providers",
        help="list provider implementations registered with the runtime API",
        description="List registered provider implementation types without loading configuration.",
        epilog="Example: keysec list-available-providers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return parser


def _format_configured_providers() -> str:
    config = load_config()
    providers = [
        (category, name, provider.type)
        for category, group in (
            ("service", config.services),
            ("crypto", config.crypto),
        )
        for name, provider in group.providers.items()
    ]
    if not providers:
        return "No providers configured."
    return "\n".join(
        f"{category}: {name} ({provider_type})"
        for category, name, provider_type in providers
    )


def _format_available_providers() -> str:
    providers = [
        (category, implementation_type)
        for category, registry in (
            ("service", service_provider_registry),
            ("crypto", crypto_provider_registry),
        )
        for implementation_type in registry.implementation_types
    ]
    if not providers:
        return "No provider implementations available."
    return "\n".join(
        f"{category}: {implementation_type}"
        for category, implementation_type in providers
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Run the KeySec command-line interface."""
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "list-available-providers":
            result = _format_available_providers()
        elif args.command == "list-providers":
            result = _format_configured_providers()
        elif args.command == "get-secret":
            keysec = KeySec()
            result = keysec.get_secret(args.secret, provider=args.provider)
        elif args.command == "generate-key":
            keysec = KeySec()
            provider = keysec.get_provider(args.provider, provider_type="crypto")
            result = provider.generate_key(args.output)
        else:
            keysec = KeySec()
            provider = keysec.get_provider(args.provider, provider_type="crypto")
            value = args.value if args.value is not None else sys.stdin.read()
            if args.command == "encrypt":
                result = provider.encrypt(value)
            else:
                result = provider.decrypt(value)
    except (KeySecError, ValueError, OSError) as exc:
        print(f"keysec: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
