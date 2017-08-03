'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expression import Expression, ArityArrow, ArityCross, A0

# primitive constants (appendix A1)
# N
zero = Expression('0', A0, True)
succ = Expression('succ', ArityArrow(A0,A0), True)
natrec = Expression('natrec', ArityArrow(ArityCross(A0,A0,ArityArrow(ArityCross(A0,A0),A0)),A0), False)
# List(A)
nil = Expression('nil', A0, True)
cons = Expression('cons', ArityArrow(A0,A0), True)
listrec = Expression('listrec', ArityArrow(ArityCross(A0,A0,ArityArrow(ArityCross(A0,A0,A0),A0)),A0), False)
# A -> B, Product(A, B)
lambda_ = Expression('lambda', ArityArrow(ArityArrow(A0,A0),A0), True)
apply = Expression('apply', ArityArrow(ArityCross(A0,A0),A0), False)
funsplit = Expression('funsplit', ArityArrow(ArityCross(A0,ArityArrow(A0,A0)),A0), False)