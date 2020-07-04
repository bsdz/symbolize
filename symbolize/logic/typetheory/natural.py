"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ...expressions.arity import A0, ArityArrow, ArityCross
from .proposition import PropositionSymbol
from .proof import ProofSymbol


class NaturalNumberProofSymbol(ProofSymbol):
    __default_arity__ = A0


N = PropositionSymbol("N", latex_repr=r"\mathbb{N}")
zero = NaturalNumberProofSymbol("0", proposition_type=N)


class succProofSymbol(ProofSymbol):
    """ [ST] p100
    """

    __default_arity__ = ArityArrow(A0, A0)

    def apply_proposition_type(self, expr):
        return N

    def compute(self, children):
        return self.apply(*children)


class primProofSymbol(ProofSymbol):
    """ [ST] p100
    note: arity does not match natrec from [BN] p197
    """

    __default_arity__ = ArityArrow(
        ArityCross(A0, A0, ArityArrow(A0, ArityArrow(A0, A0))), A0
    )

    def apply_proposition_type(self, expr):
        return expr[1].proposition_type

    def compute(self, children):
        if children[0] == zero:
            return children[1]
        elif children[0].base == succ:
            return (
                children[2]
                .apply(children[0].children[0])
                .apply(prim(children[0].children[0], children[1], children[2]))
            )
        else:
            return self


succ = succProofSymbol("succ")
prim = primProofSymbol("prim")
