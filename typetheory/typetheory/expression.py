from copy import deepcopy

from .arity import A0, ArityArrow

class ExpressionException(Exception): pass

class Expression(object):
    def __init__(self, baserepr = None, arity=A0, canonical=None):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExepression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is cannonical or not. defaults to None (ie unknown).
        """
        self.baserepr = baserepr
        self.children = None
        self.abstractions = None
        self.combination = None
        self.arity = arity
        self.canonical = canonical
    
    @staticmethod
    def combination(*combination):
        """Combines list into comma-concatenated expression.
        Args:
            combination (List[Expression]): list of expressions
        """
        expr = Expression()
        expr.combination = combination
        return expr
    
    def select(self, i):
        """
        """
        if self.combination is not None:
            return self.combination[i]
        else:
            raise ExpressionException("Cannot select from non combination")
            
    def apply(self, *children):
        if not isinstance(self.arity, ArityArrow):
            raise ExpressionException("Cannot apply when arity has no arrow")
        new_expr = deepcopy(self)
        new_expr.children = children
        new_expr.arity = self.arity.rhs
        return new_expr
    
    def abstract(self, *symbols):
        new_expr = deepcopy(self)
        new_expr.abstractions = symbols
        return new_expr
    
    def __repr__(self):
        if self.combination is not None:
            return ", ".join([repr(e) for e in self.combination])
        srepr = ""
        if self.baserepr is not None:
            srepr = self.baserepr
        if self.children is not None:
            srepr += "(%s)" % (", ".join([repr(e) for e in self.children]))
        if self.abstractions is not None:
            srepr = "(%s)%s" % (", ".join([repr(e) for e in self.abstractions]), srepr)
        return srepr
    
    def list_copies(self):
        print([k for k,v in globals().items() if v is self])

