'''
Created on 31 Jul 2017

@author: bsdz
'''
from .expression import Expression, InclusionExclusionExpression
from .definitions.sets import N

class NaturalNumber(InclusionExclusionExpression):
    def __init__(self, member_label):
        super(NaturalNumber, self).__init__('in', latexrepr=r'\in')
        new_obj = self.apply(Expression(member_label), N)
        self.__dict__.update(new_obj.__dict__)