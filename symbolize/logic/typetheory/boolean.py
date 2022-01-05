"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""
from ...expressions.arity import A0, ArityArrow, ArityCross
from .proposition import PropositionSymbol
from .proof import ProofSymbol


# true and false are members (not python True/False!)
class BooleanProofSymbol(ProofSymbol):
    __arity__ = A0


bool_ = PropositionSymbol("bool")
True_ = BooleanProofSymbol("True", proposition_type=bool_)
False_ = BooleanProofSymbol("False", proposition_type=bool_)


class IfThenElseProofSymbol(ProofSymbol):
    """ [ST] p97
    """

    __arity__ = ArityArrow(ArityCross(A0, A0, A0), A0)

    def apply_proposition_type(self, expr, **kwargs):
        return expr[1].proposition_type  # or expr[2]?

    def compute(self, children):
        if children[0] == True_:
            return children[1]
        elif children[0] == False_:
            return children[2]
        else:
            return self


ifthenelse = IfThenElseProofSymbol("ifthenelse")
