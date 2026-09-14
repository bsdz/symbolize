"""Π: dependent functions ([BN] ch. 19, [ST] §4.2 ⇒ and §4.9 ∀).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..term import Const

FAM = Arrow(A0, A0)

Pi = Const("Π", Arrow(Cross((A0, FAM)), A0))
lam = Const("λ", Arrow(FAM, A0))
apply = Const("apply", Arrow(Cross((A0, A0)), A0))

_A, _B, _b = pvar("A"), pvar("B", FAM), pvar("b", FAM)
_a, _f, _x = pvar("a"), pvar("f"), pvar("x")

PI = TypeFormer(
    former=Pi,
    # A set    B(x) set [x ∈ A]
    # ---------------------------
    #        Π(A, B) set
    formation=Signature((Param(_A, SET), Param(_B, SET, hyps=((_x, _A),))), SET),
    # b(x) ∈ B(x) [x ∈ A]
    # --------------------
    #   λ(b) ∈ Π(A, B)
    constructors=(
        (lam, Signature((Param(_b, _B(_x), hyps=((_x, _A),)),), Pi(_A, _B))),
    ),
    # f ∈ Π(A, B)    a ∈ A
    # ---------------------
    #   apply(f, a) ∈ B(a)
    eliminators=((apply, Signature((Param(_f, Pi(_A, _B)), Param(_a, _A)), _B(_a))),),
    # apply(λ(b), a) = b(a)
    computation=(Rule(apply(lam(_b), _a), _b(_a)),),
)
