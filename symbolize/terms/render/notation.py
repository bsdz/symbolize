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
EQUATION = "equation"  # a = b  for Id(A, a, b); the set is not shown
UNARY = "unary"  # -a  (one argument, symbol prefixed)
POWER = "power"  # a²  for pow(a, 2); the exponent is a natural number
NUMERAL = "numeral"  # 2  for cast(succ(succ(0))), else ↑n


@dataclass(frozen=True)
class Notation:
    """How one constant renders.

    ``precedence`` orders operators so that operands need parentheses only
    where they are ambiguous: ``x + y ⋅ z`` but ``(x + y) ⋅ z``. Infix
    operators with a precedence associate to the left. Where either side has
    no precedence every compound operand is parenthesised, as it always was.
    """

    kind: str = PREFIX
    typestring: Optional[str] = None
    latex: Optional[str] = None
    unicode: Optional[str] = None
    precedence: Optional[int] = None

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
    precedence: Optional[int] = None,
) -> Notation:
    """Register how ``const`` renders."""
    entry = Notation(kind, typestring, latex, unicode, precedence)
    _TABLE[const.name] = entry
    return entry


def lookup(const: Const) -> Notation:
    return _TABLE.get(const.name, Notation())
