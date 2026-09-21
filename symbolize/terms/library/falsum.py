"""⊥: the empty type ([BN] ch. 22 (Empty), [ST] §4.4).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Signature, TypeFormer, pvar
from ..render.notation import ATOM, notation
from ..term import Const

Falsum = Const("⊥")
abort = Const("abort", Arrow(Cross((A0, A0)), A0))
notation(Falsum, ATOM, latex=r"\bot", unicode="⊥")

_A, _p = pvar("A"), pvar("p")

FALSUM = TypeFormer(
    former=Falsum,
    formation=Signature((), SET),
    # A set    p ∈ ⊥
    # ---------------
    # abort(A, p) ∈ A
    eliminators=((abort, Signature((Param(_A, SET), Param(_p, Falsum)), _A)),),
)
