'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

from ....expressions import Symbol
from .proposition import Proposition

class Falsum(Proposition):
    proposition_expr = Symbol('⟘')
    
class Verum(Proposition):
    proposition_expr = Symbol('⟙')
    
# true and false are members (not python True/False!)
class Boolean(Proposition):
    proposition_expr = Symbol('bool')


# some generic propositions
#
class A(Proposition):
    proposition_expr = Symbol('A')

class B(Proposition):
    proposition_expr = Symbol('B')

class C(Proposition):
    proposition_expr = Symbol('C')
    