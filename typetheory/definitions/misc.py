'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol, ArityArrow, ArityCross, A0

# primitive constants (appendix A1)
# N
zero = Symbol('0', A0, True)
succ = Symbol('succ', ArityArrow(A0,A0), True)
natrec = Symbol('natrec', ArityArrow(ArityCross(A0,A0,ArityArrow(ArityCross(A0,A0),A0)),A0), False)
# List(A)
nil = Symbol('nil', A0, True)
cons = Symbol('cons', ArityArrow(A0,A0), True)
listrec = Symbol('listrec', ArityArrow(ArityCross(A0,A0,ArityArrow(ArityCross(A0,A0,A0),A0)),A0), False)
# A -> B, Product(A, B)
lambda_ = Symbol('𝜆', ArityArrow(ArityArrow(A0,A0),A0), True)
apply = Symbol('apply', ArityArrow(ArityCross(A0,A0),A0), False)
funsplit = Symbol('funsplit', ArityArrow(ArityCross(A0,ArityArrow(A0,A0)),A0), False)