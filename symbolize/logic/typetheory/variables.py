'''
Created on 3 Aug 2017

@author: bsdz
'''
from ...expressions import Symbol
from .proposition import Proposition

Falsum = Proposition('⟘')
Verum = Proposition('⟙')
    
# true and false are members (not python True/False!)
Boolean = Proposition('bool')

# some generic propositions
#
A = Proposition('A')
B = Proposition('B')
C = Proposition('C')