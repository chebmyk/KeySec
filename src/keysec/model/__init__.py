"""API-facing KeySec models and facade."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from keysec.model.keysec import KeySec

__all__ = ["KeySec"]


def __getattr__(name: str) -> object:
    if name == "KeySec":
        from keysec.model.keysec import KeySec

        return KeySec
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
