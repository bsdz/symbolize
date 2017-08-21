'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol, BinaryInfixSymbol, LogicQuantificationSymbol, ArityArrow, ArityCross, A0

forall = LogicQuantificationSymbol('forall', latex_repr=r'\forall')
exists = LogicQuantificationSymbol('exists', latex_repr=r'\exists')
or_ = BinaryInfixSymbol('or', latex_repr=r'\lor')
and_ = BinaryInfixSymbol('and', latex_repr=r'\land')
not_ = Symbol('not', arity=ArityArrow(A0,A0), latex_repr=r'\neg')
implies = BinaryInfixSymbol('implies', latex_repr=r'\Rightarrow')