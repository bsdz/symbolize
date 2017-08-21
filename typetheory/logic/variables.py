'''
Created on 3 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol
from .proposition import Proposition

class A(Proposition):
    proposition_expr = Symbol('A')

class B(Proposition):
    proposition_expr = Symbol('B')