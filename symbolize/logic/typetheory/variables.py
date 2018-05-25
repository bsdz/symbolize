'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

from .proposition import PropositionSymbol
from .proof import BooleanProofSymbol

Falsum = PropositionSymbol('⟘')
Verum = PropositionSymbol('⟙')
    
# true and false are members (not python True/False!)
bool_ = PropositionSymbol('bool')
True_ = BooleanProofSymbol('True', proposition_type=bool_)
False_ = BooleanProofSymbol('False', proposition_type=bool_)

# some generic propositions
#
A = PropositionSymbol('A')
B = PropositionSymbol('B')
C = PropositionSymbol('C')