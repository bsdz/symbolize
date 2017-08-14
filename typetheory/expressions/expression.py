from typing import List  # @UnusedImport
from copy import deepcopy
from warnings import warn
from itertools import count

from .arity import A0, ArityArrow, ArityCross
from .render.typestring import TypeStringRenderer
from .render.latex import LatexRenderer
from .render.graph import GraphRenderer
from ..utility import ToBeImplemented


class ExpressionException(Exception):
    pass

# todo: should we have different classes for CombinationExpression, AbstractExpression etc?
#       perhaps at least for a combination expression?


class ExpressionBase(object):
    pass

class ExpressionWalkResult(object):
    __slots__ = ['expr', 'part', 'listObj', 'index']
    def __init__(self, expr, part, listObj=None, index=None):
        self.expr = expr
        self.part = part
        self.listObj = listObj
        self.index = index

class FoundExpressionException(Exception):
    pass

class SimpleExpression(ExpressionBase):
    def __init__(self, baserepr=None, arity=None, canonical=None, latexrepr=None):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExpression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is canonical or not. defaults to None (ie unknown).
        """
        self.baserepr = baserepr
        self.arity = arity
        self.canonical = canonical
        self.latexrepr = latexrepr if latexrepr is not None else baserepr     
        
    def __eq__(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        if self.baserepr != other.baserepr or self.arity != other.arity:
            return False
                    
        return True

def general_bind_expression_generator():
    prefix = "__gbe_"
    for i in count(start=0, step=1):
        yield Expression('%s%s' % (prefix, i))

class Expression(ExpressionBase):
    
    # this is applied if arity not provided.
    default_arity = A0
    
    def __init__(self, baserepr=None, arity=None, canonical=None, latexrepr=None):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExpression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is canonical or not. defaults to None (ie unknown).
        """
        self._arity = arity if arity is not None else self.__class__.default_arity
        self.base = SimpleExpression(baserepr, deepcopy(self.arity), canonical, latexrepr)
        self.applications = []
        self.abstractions = []
        self.canonical = canonical
        self.parent = None # place holder for parent expression
    
    @property
    def baserepr(self):
        return self.base.baserepr
    
    @property
    def latexrepr(self):
        return self.base.latexrepr
    
    @property
    def arity(self):
        return self._arity
    
    @arity.setter
    def arity(self, value):
        warn("Setting arity outside object initialisation does not pass through to base expression")
        self._arity = value
    
    def __eq__(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        if self.baserepr != other.baserepr or self.arity != other.arity:
            return False
        
        if self.applications and other.applications:
            if not all([t == o and t.arity == o.arity for t, o in zip(self.applications, other.applications)]):
                return False
            
        if self.abstractions and other.abstractions:
            if not all([t == o and t.arity == o.arity for t, o in zip(self.abstractions, other.abstractions)]):
                return False
            
        return True
    
    def contains(self, expr):
        if self == expr:
            return True
        else:
            def search_func(wr): 
                if type(wr.expr) is Expression and wr.expr == expr:
                    raise FoundExpressionException()
            try:
                self.walk(search_func)
            except FoundExpressionException:
                return True
            return False

    def __contains__(self, expr):
        return self.contains(expr)            

    def contains_bind(self, expr):
        """checks abstractions for expr"""
        def search_func(wr): 
            if type(wr.expr) is Expression and wr.expr == expr:
                raise FoundExpressionException()
        try:
            self.walk(search_func, include_base=False, include_applications=False)
        except FoundExpressionException:
            return True
        return False

    
    def __hash__(self):
        # hash using rendered type string
        return hash(self.render_type_string())
    
    def __call__(self, *expressions: List["Expression"]) -> "Expression":
        return self.apply(*expressions)
    
    def walk(self, func, **options):
        """walks the expression, calling func on each sub part.
        func can return False to terminate the walk.
        
        Args:
            
        """
        include_base = options.get("include_base", True)
        include_applications = options.get("include_applications", True)
        include_abstractions = options.get("include_abstractions", True)
        
        if include_base:
            func(ExpressionWalkResult(self.base, 'base'))
        
        for i, expr in enumerate(self.applications):
            if include_applications:
                func(ExpressionWalkResult(expr, 'application', listObj=self.applications, index=i))
            expr.walk(func, **options)
        
        for i, expr in enumerate(self.abstractions):
            if include_abstractions:    
                func(ExpressionWalkResult(expr, 'abstraction', listObj=self.abstractions, index=i))
            expr.walk(func, **options)
       
    def apply(self, *expressions: List["Expression"]) -> "Expression":
        if not isinstance(self.arity, ArityArrow):
            raise ExpressionException("Cannot apply when arity has no arrow")
        if (len(expressions) == 1 and expressions[0].arity != self.arity.lhs) or (len(expressions) > 1 and not all([e.arity == a for e,a in zip(expressions, self.arity.lhs.args)])):
            raise ExpressionException("Cannot apply when arity arrow lhs does not match child arity")
        new_expr = deepcopy(self)
        new_expr.applications = list(deepcopy(expressions))  # todo inplace replace
        for e in new_expr.applications: e.parent = self
        new_expr.arity = self.arity.rhs  # (1) 3.8.4
        return new_expr
    
    def abstract(self, *expressions: List["Expression"]) -> "Expression":
        new_expr = deepcopy(self)
        new_expr.abstractions = list(deepcopy(expressions))  # todo inplace replace
        for e in new_expr.abstractions: e.parent = self
        new_expr.arity = ArityArrow(ArityCross(*[e.arity for e in expressions]), self.arity)  # (1) 3.8.5
        return new_expr
    
    
    def substitute(self, from_expr, to_expr: "Expression") -> "Expression":
        # todo: raise if arity differs?
        
        if self == from_expr: # exact substitution
            return deepcopy(to_expr) # (2) 2.4
        
        # check from_expr is free in this expression
        if self.contains_bind(to_expr):
            raise ToBeImplemented("Cannot yet substitute bound expression")
        
        new_expr = deepcopy(self)
        if not from_expr.applications and not from_expr.abstractions \
            and new_expr.base == from_expr.base:
            new_expr.base = to_expr # (2) 2.4
        
        for i, appl in enumerate(new_expr.applications): # (2) 2.4
            new_expr.applications[i] = appl.substitute(from_expr, to_expr)
        
        return new_expr
    
    def general_bind_form(self):
        """replaces all bound variables with general ordinal expression.
        """
        new_expr = deepcopy(self)
                
        gbe_generator = general_bind_expression_generator()
        
        def search_func(wr1): 
            # find abstraction and walk parent swaping abstracted expression
            # with generic expression
            
            gb_expr = next(gbe_generator)
            
            def swap_func(wr2):
                if wr2.expr == wr1.expr:
                    if wr2.listObj is not None:
                        wr2.listObj[wr2.index] = gb_expr
                    else:
                        pass
                        #wr2.parent.base = gb_expr # todo: perhaps reference wr2.expr directly?
                     
            new_expr.walk(swap_func)
          
        # we walk and search abstractions
        new_expr.walk(search_func, include_base=False, include_applications=False)

        return new_expr
    
    def __repr__(self):
        return self.render_type_string()
    
    def render_type_string(self):
        return TypeStringRenderer().render(self)
    
    def render_latex(self):
        return LatexRenderer().render(self)

    def render_graph(self):
        return GraphRenderer().render(self)
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.render_latex()
    
    def list_copies(self):
        print([k for k, v in globals().items() if v is self])


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
        if self.expressions and other.expressions:
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
        return self.render_type_string()
        
    def render_type_string(self):
        if self.expressions:
            rr = TypeStringRenderer()
            return ", ".join([rr.render(e) for e in self.expressions])
        
    def render_latex(self):
        if self.expressions:
            rr = LatexRenderer()
            return ", ".join([rr.render(e) for e in self.expressions])
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.render_latex()
