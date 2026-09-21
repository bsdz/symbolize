"""Bool: booleans ([BN] ch. 22 (Enumeration sets), [ST] §4.6).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..render.notation import ATOM, notation
from ..term import Const

FAM = Arrow(A0, A0)

Bool = Const("Bool")
notation(Bool, ATOM, latex=r"\mathbb{B}", unicode="𝔹", typestring="Bool")
true = Const("True")
false = Const("False")
boolrec = Const("boolrec", Arrow(Cross((FAM, A0, A0, A0)), A0))
ifthenelse = Const("ifthenelse", Arrow(Cross((A0, A0, A0)), A0))

_C, _K = pvar("C", FAM), pvar("K")
_b, _c, _d, _z = pvar("b"), pvar("c"), pvar("d"), pvar("z")

BOOL = TypeFormer(
    former=Bool,
    formation=Signature((), SET),
    constructors=(
        (true, Signature((), Bool)),
        (false, Signature((), Bool)),
    ),
    eliminators=(
        # C(z) set [z ∈ Bool]   b ∈ Bool   c ∈ C(True)   d ∈ C(False)
        # -------------------------------------------------------------
        #                  boolrec(C, b, c, d) ∈ C(b)
        (
            boolrec,
            Signature(
                (
                    Param(_C, SET, hyps=((_z, Bool),)),
                    Param(_b, Bool),
                    Param(_c, _C(true)),
                    Param(_d, _C(false)),
                ),
                _C(_b),
            ),
        ),
        # b ∈ Bool   c ∈ K   d ∈ K
        # -------------------------  ([ST] p97)
        #  ifthenelse(b, c, d) ∈ K
        (
            ifthenelse,
            Signature((Param(_b, Bool), Param(_c, _K), Param(_d, _K)), _K),
        ),
    ),
    computation=(
        Rule(boolrec(_C, true, _c, _d), _c),
        Rule(boolrec(_C, false, _c, _d), _d),
        Rule(ifthenelse(true, _c, _d), _c),
        Rule(ifthenelse(false, _c, _d), _d),
    ),
)
