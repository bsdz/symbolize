"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""
from ..expressions import Symbol, ArityArrow, ArityCross, A0

# primitive constants (appendix A1)
# N
zero = Symbol("0", A0, True)
succ = Symbol("succ", ArityArrow(A0, A0), True)
natrec = Symbol(
    "natrec",
    ArityArrow(ArityCross(A0, A0, ArityArrow(ArityCross(A0, A0), A0)), A0),
    False,
)
# List(A)
nil = Symbol("nil", A0, True)
cons = Symbol("cons", ArityArrow(A0, A0), True)
listrec = Symbol(
    "listrec",
    ArityArrow(ArityCross(A0, A0, ArityArrow(ArityCross(A0, A0, A0), A0)), A0),
    False,
)
