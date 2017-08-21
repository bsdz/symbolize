'''
Created on 31 Jul 2017

@author: bsdz
'''
from .expressions import Symbol, InclusionExclusionSymbol
from .definitions.sets import N

class NaturalNumber(InclusionExclusionSymbol):
    def __init__(self, member_label):
        super().__init__('in', latex_repr=r'\in')
        new_obj = self.apply(Symbol(member_label), N)
        self.__dict__.update(new_obj.__dict__)