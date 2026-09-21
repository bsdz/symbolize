"""Notation: how constants are displayed in each rendering style.

The table is keyed by constant name and independent of any registry, so a
term renders the same way whichever registry it is evaluated in. Library
modules register their constants; anything unregistered renders as a
prefix application of its name.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from ..term import Const

STYLES = ("typestring", "latex", "unicode")

# kinds
ATOM = "atom"  # a bare symbol: N, 0, ⊥
PREFIX = "prefix"  # name(args)
INFIX = "infix"  # a ∧ b  (two arguments)
QUANTIFIER = "quantifier"  # ∀x.B  for Q(A, (x)B)
BINDER = "binder"  # λx.b  for λ((x)b)
APPLY = "apply"  # f(a)  for apply(f, a)
TUPLE = "tuple"  # (a, b)  for pair(a, b)


@dataclass(frozen=True)
class Notation:
    kind: str = PREFIX
    typestring: Optional[str] = None
    latex: Optional[str] = None
    unicode: Optional[str] = None

    def symbol(self, style: str, default: str) -> str:
        value = getattr(self, style)
        if value is None:
            value = self.unicode if style == "typestring" else None
        return default if value is None else value


_TABLE: Dict[str, Notation] = {}


def notation(
    const: Const,
    kind: str = PREFIX,
    latex: Optional[str] = None,
    unicode: Optional[str] = None,
    typestring: Optional[str] = None,
) -> Notation:
    """Register how ``const`` renders."""
    entry = Notation(kind, typestring, latex, unicode)
    _TABLE[const.name] = entry
    return entry


def lookup(const: Const) -> Notation:
    return _TABLE.get(const.name, Notation())
