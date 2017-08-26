'''
Created on 3 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol
from .proposition import Proposition

class falsum(Proposition):
    proposition_expr = Symbol('⊥')
    
class verum(Proposition):
    proposition_expr = Symbol('⊤')
    
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
    