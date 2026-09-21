"""Σ: dependent pairs ([BN] ch. 20, [ST] §4.1 ∧ and §4.10 ∃).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..render.notation import QUANTIFIER, TUPLE, notation
from ..term import Const

FAM = Arrow(A0, A0)
STEP2 = Arrow(Cross((A0, A0)), A0)

Sigma = Const("Σ", Arrow(Cross((A0, FAM)), A0))
pair = Const("pair", Arrow(Cross((A0, A0)), A0))
split = Const("split", Arrow(Cross((FAM, A0, STEP2)), A0))
fst = Const("fst", Arrow(A0, A0))
snd = Const("snd", Arrow(A0, A0))

notation(Sigma, QUANTIFIER, latex=r"\Sigma", unicode="Σ")
notation(pair, TUPLE)

_A, _B, _C = pvar("A"), pvar("B", FAM), pvar("C", FAM)
_a, _b, _p, _e = pvar("a"), pvar("b"), pvar("p"), pvar("e", STEP2)
_x, _y, _z = pvar("x"), pvar("y"), pvar("z")

SIGMA = TypeFormer(
    former=Sigma,
    formation=Signature((Param(_A, SET), Param(_B, SET, hyps=((_x, _A),))), SET),
    # a ∈ A    b ∈ B(a)
    # ---------------------
    # pair(a, b) ∈ Σ(A, B)
    constructors=(
        (pair, Signature((Param(_a, _A), Param(_b, _B(_a))), Sigma(_A, _B))),
    ),
    eliminators=(
        # C(z) set [z ∈ Σ(A, B)]   p ∈ Σ(A, B)
        # e(x, y) ∈ C(pair(x, y)) [x ∈ A, y ∈ B(x)]
        # -------------------------------------------
        #            split(C, p, e) ∈ C(p)
        (
            split,
            Signature(
                (
                    Param(_C, SET, hyps=((_z, Sigma(_A, _B)),)),
                    Param(_p, Sigma(_A, _B)),
                    Param(_e, _C(pair(_x, _y)), hyps=((_x, _A), (_y, _B(_x)))),
                ),
                _C(_p),
            ),
        ),
        # the non-dependent projections of [ST]
        (fst, Signature((Param(_p, Sigma(_A, _B)),), _A)),
        (snd, Signature((Param(_p, Sigma(_A, _B)),), _B(fst(_p)))),
    ),
    computation=(
        Rule(split(_C, pair(_a, _b), _e), _e(_a, _b)),
        Rule(fst(pair(_a, _b)), _a),
        Rule(snd(pair(_a, _b)), _b),
    ),
)
