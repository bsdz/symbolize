'''
Created on 3 Aug 2017

@author: bsdz
'''
from ..expressions import Expression
from .proposition import Proposition

class A(Proposition):
    proposition_expr = Expression('A')

class B(Proposition):
    proposition_expr = Expression('B')