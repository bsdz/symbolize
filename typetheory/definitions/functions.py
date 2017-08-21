'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol, ArityArrow, ArityCross, A0

sin = Symbol('sin', arity=ArityArrow(A0,A0))

fst = Symbol('fst', ArityArrow(A0,A0))
snd = Symbol('snd', ArityArrow(A0,A0))
