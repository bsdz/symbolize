'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import Expression, BinaryInfixExpression, LogicQuantificationExpression, ArityArrow, ArityCross, A0

forall = LogicQuantificationExpression('forall', latexrepr=r'\forall')
exists = LogicQuantificationExpression('exists', latexrepr=r'\exists')
or_ = BinaryInfixExpression('or', latexrepr=r'\lor')
and_ = BinaryInfixExpression('and', latexrepr=r'\land')
not_ = Expression('not', arity=ArityArrow(A0,A0), latexrepr=r'\neg')
implies = BinaryInfixExpression('implies', latexrepr=r'\Rightarrow')