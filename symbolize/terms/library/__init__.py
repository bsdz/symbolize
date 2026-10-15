"""The standard library of type formers and connectives.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..decl import Registry
from . import logic, nat, order
from .bool import BOOL, Bool, boolrec, false, ifthenelse, true
from .falsum import FALSUM, Falsum, abort
from .identity import IDENTITY, Id, J, refl
from .list import LIST, List, cons, listing, listrec, nil
from .logic import and_, exists, forall, implies, not_, or_
from .nat import NAT, N, add, mul, natrec, numeral, succ, zero
from .order import ge, gt, le, lt
from .pi import PI, Pi, apply, lam
from .plus import PLUS, Plus, cases, inl, inr, when
from .sigma import SIGMA, Sigma, fst, pair, snd, split

FORMERS = (PI, SIGMA, PLUS, FALSUM, NAT, BOOL, IDENTITY, LIST)


def standard() -> Registry:
    """A fresh registry containing every former and connective."""
    registry = Registry()
    for former in FORMERS:
        registry.add_former(former)
    nat.declare(registry)
    order.declare(registry)
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
    "IDENTITY",
    "Id",
    "J",
    "refl",
    "LIST",
    "List",
    "cons",
    "listing",
    "listrec",
    "nil",
    "and_",
    "exists",
    "forall",
    "implies",
    "not_",
    "or_",
    "NAT",
    "N",
    "add",
    "mul",
    "natrec",
    "numeral",
    "succ",
    "zero",
    "ge",
    "gt",
    "le",
    "lt",
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
