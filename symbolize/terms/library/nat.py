"""N: natural numbers ([BN] ch. 7 / 19.3, [ST] §4.7).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..binding import abstract
from ..decl import SET, Param, Registry, Rule, Signature, TypeFormer, pvar
from ..render.notation import ATOM, INFIX, notation
from ..term import Abs, Const, Var

FAM = Arrow(A0, A0)
STEP2 = Arrow(Cross((A0, A0)), A0)

N = Const("N")
notation(N, ATOM, latex=r"\mathbb{N}", unicode="ℕ", typestring="N")
zero = Const("0")
succ = Const("succ", Arrow(A0, A0))
natrec = Const("natrec", Arrow(Cross((FAM, A0, A0, STEP2)), A0))

_C, _n, _d, _e = pvar("C", FAM), pvar("n"), pvar("d"), pvar("e", STEP2)
_x, _y, _z = pvar("x"), pvar("y"), pvar("z")

NAT = TypeFormer(
    former=N,
    formation=Signature((), SET),
    constructors=(
        (zero, Signature((), N)),
        (succ, Signature((Param(_n, N),), N)),
    ),
    # C(z) set [z ∈ N]   n ∈ N   d ∈ C(0)
    # e(x, y) ∈ C(succ(x)) [x ∈ N, y ∈ C(x)]
    # ----------------------------------------
    #        natrec(C, n, d, e) ∈ C(n)
    eliminators=(
        (
            natrec,
            Signature(
                (
                    Param(_C, SET, hyps=((_z, N),)),
                    Param(_n, N),
                    Param(_d, _C(zero)),
                    Param(_e, _C(succ(_x)), hyps=((_x, N), (_y, _C(_x)))),
                ),
                _C(_n),
            ),
        ),
    ),
    computation=(
        Rule(natrec(_C, zero, _d, _e), _d),
        Rule(natrec(_C, succ(_n), _d, _e), _e(_n, natrec(_C, _n, _d, _e))),
    ),
)


def numeral(k: int) -> Const:
    """The numeral ``succ(...succ(0))`` for ``k``."""
    t = zero
    for _ in range(k):
        t = succ(t)
    return t


# -- arithmetic ---------------------------------------------------------------------
#
# Addition and multiplication are definitions over natrec, recursing on the
# second argument exactly as Lean's Nat.add and Nat.mul do, so a statement
# imported from Lean about Nat.add is a statement about this plus.

# The constants are named add and mul, as in Lean; "+" alone is already the
# disjoint union former of library/plus.py. The display symbols are the
# operators.
add = Const("add", Arrow(Cross((A0, A0)), A0))
mul = Const("mul", Arrow(Cross((A0, A0)), A0))

notation(add, INFIX, latex="+", unicode="+", typestring="add")
notation(mul, INFIX, latex=r"\cdot", unicode="⋅", typestring="mul")

_m = pvar("m")
_CONST_N = Abs((A0,), N, hints=("_",))
_BINARY = Signature((Param(_m, N), Param(_n, N)), N)

# plain variables for the definition bodies: they are bound immediately, and
# their names survive only as display hints on the abstractions
_bm, _bn, _bx, _by = Var("m"), Var("n"), Var("x"), Var("y")

#  add(m, 0) = m                 add(m, succ(n)) = succ(add(m, n))
_ADD_BODY = abstract(
    natrec(_CONST_N, _bn, _bm, abstract(succ(_by), [_bx, _by])), [_bm, _bn]
)
#  mul(m, 0) = 0                 mul(m, succ(n)) = add(m, mul(m, n))
_MUL_BODY = abstract(
    natrec(_CONST_N, _bn, zero, abstract(add(_bm, _by), [_bx, _by])), [_bm, _bn]
)


def declare(registry: Registry) -> None:
    """Add arithmetic to ``registry`` (the type former is added separately)."""
    registry.define(add, _ADD_BODY, _BINARY)
    registry.define(mul, _MUL_BODY, _BINARY)
