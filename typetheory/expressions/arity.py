from typing import List
from copy import deepcopy

class ArityExpression(object):
    def repr_brackets(self):
        return '(' + repr(self) + ')'

    def copy(self):
        """A deep copy of this expression"""
        return deepcopy(self)
        
class ArityPlaceHolder(ArityExpression):
    def __eq__(self, other):
        return isinstance(other, self.__class__)
    
    def __repr__(self):
        return "∅"

    def repr_brackets(self):
        return repr(self)

A0 = ArityPlaceHolder() # convenience instance

class ArityCross(ArityExpression):
    def __init__(self, *args: List[ArityExpression]):
        self.args = args

    def __eq__(self, other):
        return isinstance(other, self.__class__) and all([t == o for t,o in zip(self.args, other.args)])

    def __repr__(self):
        return " ⨯ ".join([i.repr_brackets() for i in self.args])

class ArityArrow(ArityExpression):
    def __init__(self, lhs: ArityExpression, rhs: ArityExpression):
        self.lhs = lhs
        self.rhs = rhs

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.lhs == other.lhs and self.rhs == other.rhs
        
    def __repr__(self):
        return "%s ⟶ %s" % (self.lhs.repr_brackets(), self.rhs.repr_brackets())
    