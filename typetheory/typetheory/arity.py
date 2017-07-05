from typing import List

class ArityExpression(object):
    def repr_brackets(self):
        if repr(self) == "0":
            return "0"
        else:
            return '(' + repr(self) + ')'
        
    def __eq__(self, other):
        """Overload == and compare repr of arity expression.
        Should we implement some type of singleton for arity expression?
        Are all repr unique?
        """
        return repr(self) == repr(other)
        
class ArityPlaceHolder(ArityExpression):
    def __repr__(self):
        return "0"

A0 = ArityPlaceHolder() # convenience instance

class ArityCross(ArityExpression):
    def __init__(self, *args: List[ArityExpression]):
        self.args = args
        
    def __repr__(self):
        return " x ".join([i.repr_brackets() for i in self.args])

class ArityArrow(ArityExpression):
    def __init__(self, lhs: ArityExpression, rhs: ArityExpression):
        self.lhs = lhs
        self.rhs = rhs
        
    def __repr__(self):
        return "%s -> %s" % (self.lhs.repr_brackets(), self.rhs.repr_brackets())
    