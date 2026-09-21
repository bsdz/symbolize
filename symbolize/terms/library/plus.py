"""+: disjoint union ([BN] ch. 21, [ST] §4.3 ∨).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..render.notation import INFIX, notation
from ..term import Abs, Const
from .pi import Pi, apply

FAM = Arrow(A0, A0)

Plus = Const("+", Arrow(Cross((A0, A0)), A0))
notation(Plus, INFIX, latex="+", unicode="+")
inl = Const("inl", Arrow(A0, A0))
inr = Const("inr", Arrow(A0, A0))
when = Const("when", Arrow(Cross((FAM, A0, FAM, FAM)), A0))
cases = Const("cases", Arrow(Cross((A0, A0, A0)), A0))

_A, _B, _C, _K = pvar("A"), pvar("B"), pvar("C", FAM), pvar("K")
_a, _b, _p = pvar("a"), pvar("b"), pvar("p")
_f, _g, _x, _y, _z = pvar("f"), pvar("g"), pvar("x"), pvar("y"), pvar("z")
_F, _G = pvar("F", FAM), pvar("G", FAM)


def _const_family(body):
    """``(_)body``: a family that ignores its argument."""
    return Abs((A0,), body, hints=("_",))


PLUS = TypeFormer(
    former=Plus,
    formation=Signature((Param(_A, SET), Param(_B, SET)), SET),
    constructors=(
        (inl, Signature((Param(_a, _A),), Plus(_A, _B))),
        (inr, Signature((Param(_b, _B),), Plus(_A, _B))),
    ),
    eliminators=(
        # C(z) set [z ∈ A + B]   p ∈ A + B
        # F(x) ∈ C(inl(x)) [x ∈ A]   G(y) ∈ C(inr(y)) [y ∈ B]
        # ----------------------------------------------------
        #              when(C, p, F, G) ∈ C(p)
        (
            when,
            Signature(
                (
                    Param(_C, SET, hyps=((_z, Plus(_A, _B)),)),
                    Param(_p, Plus(_A, _B)),
                    Param(_F, _C(inl(_x)), hyps=((_x, _A),)),
                    Param(_G, _C(inr(_y)), hyps=((_y, _B),)),
                ),
                _C(_p),
            ),
        ),
        # p ∈ A + B    f ∈ A ⇒ K    g ∈ B ⇒ K
        # ------------------------------------  ([ST] p81)
        #          cases(p, f, g) ∈ K
        (
            cases,
            Signature(
                (
                    Param(_p, Plus(_A, _B)),
                    Param(_f, Pi(_A, _const_family(_K))),
                    Param(_g, Pi(_B, _const_family(_K))),
                ),
                _K,
            ),
        ),
    ),
    computation=(
        Rule(when(_C, inl(_a), _F, _G), _F(_a)),
        Rule(when(_C, inr(_b), _F, _G), _G(_b)),
        Rule(cases(inl(_a), _f, _g), apply(_f, _a)),
        Rule(cases(inr(_b), _f, _g), apply(_g, _b)),
    ),
)
