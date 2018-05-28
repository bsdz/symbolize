'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

from .proposition import PropositionSymbol

Falsum = PropositionSymbol('⟘')
Verum = PropositionSymbol('⟙')
    
# some generic propositions
#
A = PropositionSymbol('A')
B = PropositionSymbol('B')
C = PropositionSymbol('C')