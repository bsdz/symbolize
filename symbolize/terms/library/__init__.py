"""The standard library of type formers and connectives.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..decl import Registry
from . import logic
from .bool import BOOL, Bool, boolrec, false, ifthenelse, true
from .falsum import FALSUM, Falsum, abort
from .logic import and_, exists, forall, implies, not_, or_
from .nat import NAT, N, natrec, numeral, succ, zero
from .pi import PI, Pi, apply, lam
from .plus import PLUS, Plus, cases, inl, inr, when
from .sigma import SIGMA, Sigma, fst, pair, snd, split

FORMERS = (PI, SIGMA, PLUS, FALSUM, NAT, BOOL)


def standard() -> Registry:
    """A fresh registry containing every former and connective."""
    registry = Registry()
    for former in FORMERS:
        registry.add_former(former)
    logic.declare(registry)
    return registry


STANDARD = standard()

__all__ = [
    "BOOL",
    "Bool",
    "boolrec",
    "false",
    "ifthenelse",
    "true",
    "FALSUM",
    "Falsum",
    "abort",
    "and_",
    "exists",
    "forall",
    "implies",
    "not_",
    "or_",
    "NAT",
    "N",
    "natrec",
    "numeral",
    "succ",
    "zero",
    "PI",
    "Pi",
    "apply",
    "lam",
    "PLUS",
    "Plus",
    "cases",
    "inl",
    "inr",
    "when",
    "SIGMA",
    "Sigma",
    "fst",
    "pair",
    "snd",
    "split",
    "FORMERS",
    "STANDARD",
    "standard",
]
