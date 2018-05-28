'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
from .proposition import PropositionSymbol
from .proof import ProofSymbol, A0

# true and false are members (not python True/False!)
class BooleanProofSymbol(ProofSymbol):
    __default_arity__ = A0  

bool_ = PropositionSymbol('bool')
True_ = BooleanProofSymbol('True', proposition_type=bool_)
False_ = BooleanProofSymbol('False', proposition_type=bool_)
