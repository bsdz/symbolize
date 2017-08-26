'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol, ArityArrow, ArityCross, A0

sin = Symbol('sin', arity=ArityArrow(A0,A0))

fst = Symbol('fst', ArityArrow(A0,A0))
snd = Symbol('snd', ArityArrow(A0,A0))
inl = Symbol('inl', ArityArrow(A0,A0))
inr = Symbol('inr', ArityArrow(A0,A0))
cases = Symbol('cases', ArityArrow(ArityCross(A0,A0,A0), A0))