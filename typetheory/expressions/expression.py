""" todo: should we have different classes for CombinationExpression, AbstractExpression etc?
       perhaps at least for a combination expression?
"""
from typing import List  # @UnusedImport
from copy import deepcopy
from warnings import warn
from itertools import count

from .arity import A0, ArityArrow, ArityCross
from .render.typestring import TypeStringRenderer, TypeStringRendererMixin
from .render.latex import LatexRenderer, LatexRendererExpressionMixin
from .render.graph import GraphRenderer
from ..utility import ToBeImplemented

class ExpressionWalkResult(object):
    __slots__ = ['expr', 'obj', 'index']
    def __init__(self, expr, obj=None, index=None):
        self.expr = expr
        self.obj = obj
        self.index = index
        
    def __repr__(self):
        res = "expr: %s; part: %s" % (repr(self.expr),self.part)
        if self.obj is not None:
            res += "; obj: %s" % self.obj
            if self.index is not None:
                res += "[%s]" % self.index
        res += "; type: %s" % self.expr.__class__.__name__
        if self.expr.parent is not None:
            res += "; parent_type: %s" % self.expr.parent.__class__.__name__
        return "ExpressionWalkResult(%s)" % res

def general_bind_expression_generator():
    prefix = "__gbe_"
    for i in count(start=0, step=1): # we have an infinite collection of variables
        yield Expression('%s%s' % (prefix, i))

class FoundExpressionException(Exception):
    pass

class ExpressionException(Exception):
    pass

class Expression(TypeStringRendererMixin):
    def __init__(self):
        self.parent = None
        
    def __repr__(self):
        return self.render_type_string()
    
    def __call__(self, *expressions: List["Expression"]) -> "Expression":
        return self.apply(*expressions)
    
    def __eq__(self, other):
        """Overload == and compare expressions.
        """
        return self.equals(other)
    
    def __hash__(self):
        # hash using rendered type string
        return hash(self.render_type_string())
    
    def __contains__(self, expr):
        return self.contains(expr)
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.render_latex()
    
    def render_type_string(self):
        return TypeStringRenderer().render(self)
    
    def render_latex(self):
        return LatexRenderer().render(self)

    def render_graph(self):
        return GraphRenderer().render(self)
    
    def list_copies(self):
        # todo: is this useful?
        print([k for k, v in globals().items() if v is self])
        
    def apply(self, *expressions: List["Expression"]) -> "Expression":
        if not isinstance(self.arity, ArityArrow):
            raise ExpressionException("Cannot apply when arity has no arrow")
        if (len(expressions) == 1 and expressions[0].arity != self.arity.lhs) or (len(expressions) > 1 and not all([e.arity == a for e,a in zip(expressions, self.arity.lhs.args)])):
            raise ExpressionException("Cannot apply when arity arrow lhs does not match child arity")
        return ApplicationExpression(self, expressions, self.arity.rhs) # arity - (1) 3.8.4
    
    def abstract(self, *expressions: List["Expression"]) -> "Expression":
        return AbstractionExpression(self, expressions, ArityArrow(ArityCross(*[e.arity for e in expressions]), self.arity)) # arity - (1) 3.8.5
    
    def walk(self, func, **options):
        """walks the expression, calling func on each sub part.
        func can return False to terminate the walk.
        
        abstract method.
        """
        raise NotImplementedError()
    
    def contains(self, expr):
        if self == expr:
            return True
        else:
            def search_func(wr): 
                if wr.expr == expr:
                    raise FoundExpressionException()
            try:
                self.walk(search_func)
            except FoundExpressionException:
                return True
            return False
        
    def contains_bind(self, expr):
        """checks abstractions for expr"""
        def search_func(wr): 
            if type(wr.expr.parent) is AbstractionExpression and wr.expr == expr:
                raise FoundExpressionException()
        try:
            self.walk(search_func)
        except FoundExpressionException:
            return True
        return False
    
    def substitute(self, from_expr, to_expr: "Expression") -> "Expression":
        """abstract method"""
        raise NotImplementedError()
    
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
                    # should we adjust arity to match?
                    gb_expr._arity = wr2.expr.arity
                    if wr2.index is not None:
                        wr2.obj[wr2.index] = gb_expr
                    else:
                        wr2.obj.base = gb_expr
                     
            new_expr.walk(swap_func)
          
        # we walk and search abstractions
        new_expr.walk(search_func, include_base=False, include_applications=False)

        return new_expr
        
    def beta_reduction(self):
        """beta-reduce expression, ie apply to abstraction
        """
        foo = self.arity
        pass


class Symbol(Expression):
    def __init__(self, str_repr=None, arity=A0, canonical=None, latex_repr=None):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExpression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is canonical or not. defaults to None (ie unknown).
        """
        super().__init__()
        self.str_repr = str_repr
        self.latex_repr = latex_repr if latex_repr is not None else str_repr
        self.arity = arity
        self.canonical = canonical

    def render_typestring(self, renderer):  # @UnusedVariable
        return self.str_repr
    
    def equals(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        return isinstance(other, self.__class__) and self.str_repr == other.str_repr and self.arity == other.arity
    
    def walk(self, func, **options):  # @UnusedVariable
        pass
    
    def substitute(self, from_expr, to_expr: "Expression") -> "Expression":
        return deepcopy(to_expr)  if self == from_expr else deepcopy(self) #  exact substitution - (2) 2.4

class BaseWithChildrenExpression(Expression):
    def __init__(self, base: "ExpressionBase", expressions: List["ExpressionBase"], arity):
        super().__init__()
        self.base = deepcopy(base)
        self.children = list(deepcopy(expressions))
        for e in self.children: e.parent = self
        self.arity = deepcopy(arity)
    
    def equals(self, other):
        """Following (1) 3.9.
        """
        # todo: convert to general bind form before comparison (make optional?)
        if not isinstance(other, self.__class__):
            return False
        
        if self.base != other.base:
            return False
        
        if self.children and other.children: # todo: do we need to check arity here?
            if not all([t == o and t.arity == o.arity for t, o in zip(self.children, other.children)]):
                return False
        return True
    
    def walk(self, func, **options):  # @UnusedVariable
        func(ExpressionWalkResult(self.base, obj=self))
        self.base.walk(func, **options)
        for i, expr in enumerate(self.children):
            func(ExpressionWalkResult(expr, obj=self.children, index=i))
            expr.walk(func, **options)
            
    def substitute(self, from_expr, to_expr: "Expression") -> "Expression":
        
        if self == from_expr: # exact substitution
            return deepcopy(to_expr) # (2) 2.4
        
        # check from_expr is free in this expression
        if self.contains_bind(to_expr):
            raise ToBeImplemented("Cannot yet substitute bound expression")
        
        new_expr = deepcopy(self)
        new_expr.base = new_expr.base.substitute(from_expr, to_expr) # (2) 2.4
        
        for i, child in enumerate(new_expr.children): # (2) 2.4
            new_expr.children[i] = child.substitute(from_expr, to_expr)
        
        return new_expr

class ApplicationExpression(BaseWithChildrenExpression):
    def render_typestring(self, renderer):
        return "%s(%s)" % (renderer.render(self.base), ", ".join([renderer.render(e) for e in self.children]))

class AbstractionExpression(BaseWithChildrenExpression):
    def render_typestring(self, renderer):
        return "(%s)%s" % (", ".join([renderer.render(e) for e in self.children]), renderer.render(self.base))


class Expression2(Expression):
    
    # this is applied if arity not provided.
    default_arity = A0


    @property
    def arity(self):
        return self._arity
    
    @arity.setter
    def arity(self, value):
        warn("Setting arity outside object initialisation does not pass through to base expression")
        self._arity = value

    


# class ExpressionCombination(ExpressionBase):    
#     def __init__(self, *expressions: List[Expression]):
#         """Combines list into comma-concatenated expression.
#         Args:
#             expressions (List[Expression]): list of expressions
#         """
#         self.expressions = expressions
#         self._arity = ArityCross(*[e.arity for e in expressions]) # (1) 3.8.6
#         
#     def __eq__(self, other):
#         """Overload == and compare expressions.
#         Following (1) 3.9.
#         """
#         # combinations are dealt with separately
#         if self.expressions and other.expressions:
#             return all([t == o and t.arity == o.arity for t,o in zip(self.expressions, other.expressions)])
#         
#     def select(self, i: int) -> Expression:
#         """Selects indexed subexpression from expression.
#         Args:
#             i (int): integer subexpression
#         """
#         if self.expressions is not None:
#             new_expr = deepcopy(self.expressions[i])
#             new_expr._arity = self.arity.args[i] # (1) 3.8.7
#             return new_expr
#         
#     def __repr__(self):
#         return self.render_type_string()
# 
#     @property
#     def arity(self):
#         return self._arity
#         
#     def render_type_string(self):
#         if self.expressions:
#             rr = TypeStringRenderer()
#             return ", ".join([rr.render(e) for e in self.expressions])
#         
#     def render_latex(self):
#         if self.expressions:
#             rr = LatexRenderer()
#             return ", ".join([rr.render(e) for e in self.expressions])
    
