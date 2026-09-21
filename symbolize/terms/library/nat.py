"""N: natural numbers ([BN] ch. 7 / 19.3, [ST] §4.7).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..render.notation import ATOM, notation
from ..term import Const

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


def numeral(k: int):
    """The numeral ``succ(...succ(0))`` for ``k``."""
    t = zero
    for _ in range(k):
        t = succ(t)
    return t
