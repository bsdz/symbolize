'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol, BinaryInfixSymbol, LogicQuantificationSymbol, ArityArrow, ArityCross, A0

forall = LogicQuantificationSymbol('∀', latex_repr=r'\forall')
exists = LogicQuantificationSymbol('∃', latex_repr=r'\exists')
or_ = BinaryInfixSymbol('∨', latex_repr=r'\lor')
and_ = BinaryInfixSymbol('∧', latex_repr=r'\land')
not_ = Symbol('\u2a3c', arity=ArityArrow(A0,A0), latex_repr=r'\neg')
implies = BinaryInfixSymbol('⟹', latex_repr=r'\Rightarrow')
then = BinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
iff = BinaryInfixSymbol('⟺', latex_repr=r'\iff')