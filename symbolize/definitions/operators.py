'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
from ..expressions import BinaryInfixSymbol, InclusionExclusionSymbol


plus = BinaryInfixSymbol('+')
mult = BinaryInfixSymbol('⨯', latex_repr=r'\cdot')
divide = BinaryInfixSymbol('/')

gt = BinaryInfixSymbol('>', latex_repr=r'>')
geq = BinaryInfixSymbol('≥', latex_repr=r'\geq')
lt = BinaryInfixSymbol('<', latex_repr=r'<')
leq = BinaryInfixSymbol('≤', latex_repr=r'\leq')


in_ = InclusionExclusionSymbol('∈', latex_repr=r'\in')

pair = BinaryInfixSymbol(',')

