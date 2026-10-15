"""The order on N, as abbreviations over Σ, Id and addition:

    m ≤ n  :=  Σ(N, (k)Id(N, add(m, k), n))      "some k has m + k = n"
    m < n  :=  succ(m) ≤ n
    m ≥ n  :=  n ≤ m
    m > n  :=  n < m

The legacy ``definitions/operators.py`` supplied ``leq``/``geq``/``lt``/``gt``
as bare symbols with no content; these are propositions that can be proved
and computed with.

Two consequences of defining ``≤`` this way are worth stating.

Because ``exists`` here is a strong Σ, a proof of ``m ≤ n`` yields the
difference: ``fst`` of it is a ``k`` with ``m + k = n``. That is deliberate
(see AGENTS.md §1) and is why ``add`` recursing on its *second* argument
matters: ``add(n, 0)`` reduces to ``n``, so ``n ≤ n`` is witnessed by
``pair(0, refl(n))`` with no induction at all. The other orientation would
have made reflexivity need a proof by induction.

It also means Lean's ``Nat.le`` must not be mapped onto this constant
without thought: ``Nat.le`` is a proof-irrelevant ``Prop``, so an imported
proof is an opaque constant and projecting a witness out of it is stuck
rather than wrong -- the same argument that licenses ``Eq`` ↦ ``Id`` in
``interop/lean.py`` -- but the importer deliberately refuses ``LE.le`` until
that is decided.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..binding import abstract
from ..decl import SET, Param, Registry, Signature, pvar
from ..render.notation import INFIX, notation
from ..term import Const, Var
from .identity import Id
from .nat import N, add, succ
from .sigma import Sigma

BINARY = Arrow(Cross((A0, A0)), A0)

le = Const("≤", BINARY)
lt = Const("<", BINARY)
ge = Const("≥", BINARY)
gt = Const(">", BINARY)

notation(le, INFIX, latex=r"\leq", unicode="≤", typestring="le")
notation(lt, INFIX, latex="<", unicode="<", typestring="lt")
notation(ge, INFIX, latex=r"\geq", unicode="≥", typestring="ge")
notation(gt, INFIX, latex=">", unicode=">", typestring="gt")

_m, _n = pvar("m"), pvar("n")
_RELATION = Signature((Param(_m, N), Param(_n, N)), SET)

# plain variables for the definition bodies: they are bound immediately, and
# their names survive only as display hints on the abstractions
_bm, _bn, _bk = Var("m"), Var("n"), Var("k")

#  m ≤ n  :=  Σ(N, (k)Id(N, m + k, n))
_LE_BODY = abstract(
    Sigma(N, abstract(Id(N, add(_bm, _bk), _bn), [_bk])), [_bm, _bn]
)
_LT_BODY = abstract(le(succ(_bm), _bn), [_bm, _bn])
_GE_BODY = abstract(le(_bn, _bm), [_bm, _bn])
_GT_BODY = abstract(lt(_bn, _bm), [_bm, _bn])


def declare(registry: Registry) -> None:
    """Add the order relations to ``registry``."""
    registry.define(le, _LE_BODY, _RELATION)
    registry.define(lt, _LT_BODY, _RELATION)
    registry.define(ge, _GE_BODY, _RELATION)
    registry.define(gt, _GT_BODY, _RELATION)
