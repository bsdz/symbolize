'''
Created on 31 Jul 2017

@author: bsdz
'''
from .expressions import Symbol, A0
from .expressions.extensions import InclusionExclusionExpression
from .definitions.operators import in_
from .definitions.sets import N


class NaturalNumber(InclusionExclusionExpression):
    def __init__(self, member_label):
        super().__init__(in_, [Symbol(member_label), N], A0)
        