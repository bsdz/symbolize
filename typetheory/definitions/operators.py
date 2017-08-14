'''
Created on 2 Aug 2017

@author: bsdz
'''
from ..expressions import BinaryInfixExpression, InclusionExclusionExpression, Expression, ArityArrow, ArityCross, A0


plus = BinaryInfixExpression('+')
mult = BinaryInfixExpression('*', latexrepr=r'\cdot')
divide = BinaryInfixExpression('/')

gt = BinaryInfixExpression('>', latexrepr=r'>')
geq = BinaryInfixExpression('>=', latexrepr=r'\geq')
lt = BinaryInfixExpression('<', latexrepr=r'<')
leq = BinaryInfixExpression('<=', latexrepr=r'\leq')


in_ = InclusionExclusionExpression('in', latexrepr=r'\in')

pair = BinaryInfixExpression(',')

