"""The standard library of type formers and connectives.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..decl import Registry
from . import identity, logic, nat, order, real
from .bool import BOOL, Bool, boolrec, false, ifthenelse, true
from .falsum import FALSUM, Falsum, abort
from .identity import IDENTITY, Id, J, refl
from .list import LIST, List, cons, listing, listrec, nil
from .logic import and_, exists, forall, implies, not_, or_
from .nat import NAT, N, add, mul, natrec, numeral, succ, zero
from .order import ge, gt, le, lt
from .pi import PI, Pi, apply, lam
from .plus import PLUS, Plus, cases, inl, inr, when
from .real import REAL, R
from .ring import CommRing, commutative_ring
from .sigma import SIGMA, Sigma, fst, pair, snd, split

FORMERS = (PI, SIGMA, PLUS, FALSUM, NAT, BOOL, IDENTITY, LIST)


def standard(reals: bool = False) -> Registry:
    """A fresh registry containing every former and connective.

    ``reals`` adds ``R`` with the commutative ring axioms. They are axioms,
    believed rather than proved, so they are opt-in: a registry without them
    has no axioms at all.
    """
    registry = Registry()
    for former in FORMERS:
        registry.add_former(former)
    identity.declare(registry)
    nat.declare(registry)
    order.declare(registry)
    logic.declare(registry)
    if reals:
        real.declare(registry)
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
    "REAL",
    "R",
    "CommRing",
    "commutative_ring",
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
