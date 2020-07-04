"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""
from ..expressions import Symbol, ArityArrow, ArityCross, A0
from ..expressions.extensions import LambdaSymbol

sin = Symbol("sin", arity=ArityArrow(A0, A0))

# takes a pair and returns a singleton
fst = Symbol("fst", ArityArrow(ArityCross(A0, A0), A0))
# takes a pair and returns a singleton
snd = Symbol("snd", ArityArrow(ArityCross(A0, A0), A0))
inl = Symbol("inl", ArityArrow(A0, A0))
inr = Symbol("inr", ArityArrow(A0, A0))
cases = Symbol("cases", ArityArrow(ArityCross(A0, A0, A0), A0))

# A -> B, Product(A, B)
lambda_ = LambdaSymbol("𝜆", ArityArrow(ArityArrow(A0, A0), A0), True)
apply = Symbol("apply", ArityArrow(ArityCross(A0, A0), A0), False)
funsplit = Symbol("funsplit", ArityArrow(ArityCross(A0, ArityArrow(A0, A0)), A0), False)
