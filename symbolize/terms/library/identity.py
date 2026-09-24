"""Id: the identity (equality) set ([BN] ch. 8, [ST] §5.3).

``Id(A, a, b)`` is the set of proofs that ``a`` and ``b`` are equal elements
of ``A``. Its only canonical inhabitant is ``refl(a) : Id(A, a, a)``, and its
eliminator ``J`` (``idpeel`` in [BN]) lets a family indexed by both endpoints
and by the proof be established from the reflexive case alone.

This is *propositional* equality, and is weaker than the definitional
equality decided by ``Evaluator.defeq``: ``plus(m, 0)`` and ``m`` are equal
definitionally only when the recursion can fire, whereas an inhabitant of
``Id(N, plus(m, 0), m)`` holds for a variable ``m`` as well -- but has to be
proved (or imported).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..render.notation import EQUATION, PREFIX, notation
from ..term import Const

FAM3 = Arrow(Cross((A0, A0, A0)), A0)
FAM = Arrow(A0, A0)

Id = Const("Id", Arrow(Cross((A0, A0, A0)), A0))
refl = Const("refl", Arrow(A0, A0))
J = Const("J", Arrow(Cross((FAM3, A0, FAM)), A0))

notation(Id, EQUATION, latex="=", unicode="=", typestring="Id")
notation(refl, PREFIX)

_A, _a, _b, _c = pvar("A"), pvar("a"), pvar("b"), pvar("c")
_C, _d = pvar("C", FAM3), pvar("d", FAM)
_x, _y, _z = pvar("x"), pvar("y"), pvar("z")

IDENTITY = TypeFormer(
    former=Id,
    # A set    a ∈ A    b ∈ A
    # -------------------------
    #     Id(A, a, b) set
    formation=Signature((Param(_A, SET), Param(_a, _A), Param(_b, _A)), SET),
    #      a ∈ A
    # ---------------------
    # refl(a) ∈ Id(A, a, a)
    constructors=((refl, Signature((Param(_a, _A),), Id(_A, _a, _a))),),
    eliminators=(
        # C(x, y, z) set [x ∈ A, y ∈ A, z ∈ Id(A, x, y)]
        # c ∈ Id(A, a, b)    d(x) ∈ C(x, x, refl(x)) [x ∈ A]
        # ---------------------------------------------------
        #             J(C, c, d) ∈ C(a, b, c)
        (
            J,
            Signature(
                (
                    Param(
                        _C,
                        SET,
                        hyps=((_x, _A), (_y, _A), (_z, Id(_A, _x, _y))),
                    ),
                    Param(_c, Id(_A, _a, _b)),
                    Param(_d, _C(_x, _x, refl(_x)), hyps=((_x, _A),)),
                ),
                _C(_a, _b, _c),
            ),
        ),
    ),
    # J(C, refl(a), d) = d(a)
    computation=(Rule(J(_C, refl(_a), _d), _d(_a)),),
)
