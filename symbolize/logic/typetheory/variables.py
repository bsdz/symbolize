'''
Created on 3 Aug 2017

@author: bsdz
'''
from .proposition import PropositionSymbol

Falsum = PropositionSymbol('⟘')
Verum = PropositionSymbol('⟙')
    
# true and false are members (not python True/False!)
Boolean = PropositionSymbol('bool')

# some generic propositions
#
A = PropositionSymbol('A')
B = PropositionSymbol('B')
C = PropositionSymbol('C')