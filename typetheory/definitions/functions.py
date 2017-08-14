'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Expression, ArityArrow, ArityCross, A0

sin = Expression('sin', arity=ArityArrow(A0,A0))

fst = Expression('fst', ArityArrow(A0,A0))
snd = Expression('snd', ArityArrow(A0,A0))
