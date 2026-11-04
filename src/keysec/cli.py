"""Command-line interface for KeySec."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from keysec import KeySec
from keysec.model.errors import KeySecError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="keysec")
    commands = parser.add_subparsers(dest="command", required=True)

    get_secret = commands.add_parser(
        "get-secret",
        help="retrieve a secret using a configured service provider",
    )
    get_secret.add_argument("secret", help="secret name or wrapped secret reference")
    get_secret.add_argument(
        "--provider",
        help="configured service provider name (defaults to keysec.services.default)",
    )

    generate_key = commands.add_parser(
        "generate-key",
        help="generate a key using a configured crypto provider",
    )
    generate_key.add_argument(
        "--provider",
        required=True,
        help="configured crypto provider name",
    )
    generate_key.add_argument(
        "--output",
        help="key file path (defaults to the provider's configured key_file)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the KeySec command-line interface."""
    args = _build_parser().parse_args(argv)
    try:
        keysec = KeySec()
        if args.command == "get-secret":
            result = keysec.get_secret(args.secret, provider=args.provider)
        else:
            provider = keysec.get_provider(args.provider, provider_type="crypto")
            result = provider.generate_key(args.output)
    except (KeySecError, ValueError, OSError) as exc:
        print(f"keysec: {exc}", file=sys.stderr)
        return 1

    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
