from typing import List
from copy import deepcopy

from .arity import A0, ArityArrow, ArityCross
from .render.typestring import TypeStringRenderer
from .render.latex import LatexRenderer
from .render.graph import GraphRenderer


class ExpressionException(Exception):
    pass

# todo: should we have different classes for CombinationExpression, AbstractExpression etc?
#       perhaps at least for a combination expression?


class ExpressionBase(object):
    pass


class Expression(ExpressionBase):
    
    # this is applied if arity not provided.
    default_arity = A0
    
    def __init__(self, baserepr = None, arity=None, canonical=None, latexrepr=None):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExpression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is cannonical or not. defaults to None (ie unknown).
        """
        self.baserepr = baserepr
        self.applications = None
        self.abstractions = None
        self.arity = arity if arity is not None else self.__class__.default_arity
        self.canonical = canonical
        self.latexrepr = latexrepr if latexrepr is not None else baserepr
        
    def __eq__(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        if self.baserepr != other.baserepr or self.arity != other.arity:
            return False
        
        if self.applications is not None and other.applications is not None:
            if not all([t == o and t.arity == o.arity for t,o in zip(self.applications, other.applications)]):
                return False
            
        if self.abstractions is not None and other.abstractions is not None:
            if not all([t == o and t.arity == o.arity for t,o in zip(self.abstractions, other.abstractions)]):
                return False
            
        return True
       
    def apply(self, *expressions: List["Expression"]) -> "Expression":
        if not isinstance(self.arity, ArityArrow):
            raise ExpressionException("Cannot apply when arity has no arrow")
        if not all([e.arity == a for e,a in zip(expressions, self.arity.lhs.args)]):
            raise ExpressionException("Cannot apply when arity arrow lhs does not match child arity")
        new_expr = deepcopy(self)
        new_expr.applications = expressions
        new_expr.arity = self.arity.rhs # (1) 3.8.4
        return new_expr
    
    def abstract(self, *expressions: List["Expression"]) -> "Expression":
        new_expr = deepcopy(self)
        new_expr.abstractions = expressions
        new_expr.arity = ArityArrow(ArityCross(*[e.arity for e in expressions]),self.arity) # (1) 3.8.5
        return new_expr
    
    def __repr__(self):
        return self.render_type_string()
    
    def render_type_string(self):
        return TypeStringRenderer(self).render()
    
    def render_latex(self):
        return LatexRenderer(self).render()
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.render_latex()
    
    def list_copies(self):
        print([k for k,v in globals().items() if v is self])


class ExpressionCombination(ExpressionBase):    
    def __init__(self, *expressions: List[Expression]):
        """Combines list into comma-concatenated expression.
        Args:
            expressions (List[Expression]): list of expressions
        """
        self.expressions = expressions
        self.arity = ArityCross(*[e.arity for e in expressions]) # (1) 3.8.6
        
    def __eq__(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        # combinations are dealt with separately
        if self.expressions is not None and other.expressions is not None:
            return all([t == o and t.arity == o.arity for t,o in zip(self.expressions, other.expressions)])
        
    def select(self, i: int) -> Expression:
        """Selects indexed subexpression from expression.
        Args:
            i (int): integer subexpression
        """
        if self.expressions is not None:
            new_expr = deepcopy(self.expressions[i])
            new_expr.arity = self.arity.args[i] # (1) 3.8.7
            return new_expr
        
    def __repr__(self):
        if self.expressions is not None:
            return ", ".join([repr(e) for e in self.expressions])
