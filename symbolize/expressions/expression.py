""" todo: should we have different classes for CombinationExpression, AbstractExpression etc?
       perhaps at least for a combination expression?
"""
from typing import List  # @UnusedImport
from copy import deepcopy
from warnings import warn
from itertools import count
from functools import wraps

from .arity import A0, ArityArrow, ArityCross
from .render.typestring import TypeStringRenderer, TypeStringRendererMixin
from .render.latex import LatexRenderer, LatexRendererMixin
from .render.graph import GraphToolRenderer, GraphToolRendererMixin
from ..utility import ToBeImplemented

def alias_render_typestring(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._str_repr_alias is not None:
            return self._str_repr_alias
        return f(self, *args, **kwargs)
    return wrapper

def alias_render_latex(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._latex_repr_alias is not None:
            return self._latex_repr_alias
        return f(self, *args, **kwargs)
    return wrapper

class ExpressionWalkResult(object):
    __slots__ = ['expr', 'obj', 'index']
    def __init__(self, expr, obj=None, index=None):
        self.expr = expr
        self.obj = obj
        self.index = index
        
    def __repr__(self):
        res = "expr: %s" % (repr(self.expr))
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
        yield Symbol('%s%s' % (prefix, i))

class FoundExpressionException(Exception):
    pass

class ExpressionException(Exception):
    pass

APPLY_LEFT_BRACKET = '('
APPLY_RIGHT_BRACKET = ')'
ABSTRACT_LEFT_BRACKET = '('
ABSTRACT_RIGHT_BRACKET = ')'

class ExpressionMetaClass(type):
    def __new__(cls, clsname, bases, dct, **kwargs):
        expression_base_class = kwargs.pop("expression_base_class", None)
        if expression_base_class is not None:
            bases = bases + (expression_base_class,)
        new_type = type.__new__(cls, clsname, bases, dct)
        if kwargs.pop("default_abstraction_class", False):
            cls.__default_abstraction_class__ = new_type
        if kwargs.pop("default_application_class", False):
            cls.__default_application_class__ = new_type
        return new_type

class Expression(TypeStringRendererMixin, LatexRendererMixin, GraphToolRendererMixin, metaclass=ExpressionMetaClass):
    def __init__(self):
        self.parent = None
        self._arity = None
        self._str_repr_alias = None
        self._latex_repr_alias = None
        
    def __repr__(self):
        return self.repr_typestring()
    
    def __call__(self, *args, **kwargs):
        return self.apply(*args, **kwargs)
    
    def __eq__(self, other):
        """Overload == and compare expressions.
        """
        return self.equals(other)
    
    def __hash__(self):
        # hash using rendered type string
        return hash(self.repr_typestring())
    
    def __contains__(self, expr):
        return self.contains(expr)
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.repr_latex()
    
    def repr_typestring(self):
        return TypeStringRenderer().render(self)
    
    def repr_latex(self):
        return LatexRenderer().render(self)

    def repr_graphtool(self):
        return GraphToolRenderer().render(self)

    @property
    def arity(self):
        return self._arity
    
    @arity.setter
    def arity(self, value):
        warn("Setting arity outside object initialisation does not pass through to base expression")
        self._arity = value
        
    def alias(self, str_repr, latex_repr=None):
        new_alias = self.copy()
        new_alias._str_repr_alias = str_repr
        new_alias._latex_repr_alias = str_repr if latex_repr is None else latex_repr
        return new_alias
    
    def list_copies(self):
        # todo: is this useful?
        print([k for k, v in globals().items() if v is self])

    def copy(self):
        """A deep copy of this expression"""
        return deepcopy(self)
     
    def default_application_class(self):
        if hasattr(self.__class__, "__default_application_class__"):
            return self.__class__.__default_application_class__
        else:
            return type(self.__class__).__default_application_class__
    
    def default_abstraction_class(self):
        if hasattr(self.__class__, "__default_abstraction_class__"):
            return self.__class__.__default_abstraction_class__
        else:
            return type(self.__class__).__default_abstraction_class__
        
    def apply(self, *expressions: List["Expression"], check_arity=True, application_kwargs={}) -> "Expression":
        if check_arity: # todo: do we need this?
            if not isinstance(self.arity, ArityArrow):
                raise ExpressionException("Cannot apply when arity has no arrow: %s" % self.arity)
            if len(expressions) == 1 and expressions[0].arity != self.arity.lhs:
                raise ExpressionException("Cannot apply when arity arrow lhs does not match child arity: %s ≠ %s" % (self.arity.lhs, expressions[0].arity))
            if len(expressions) > 1 and not all([e.arity == a for e,a in zip(expressions, self.arity.lhs.args)]):
                raise ExpressionException("Cannot apply when arity arrow lhs does not match child arity: %s ≠ %s" % (self.arity.lhs, ArityCross(*[e.arity for e in expressions])))
        else:
            warn("Skipping arity check on apply")
        return self.default_application_class()(self, expressions, self.arity.rhs, **application_kwargs) # arity - (1) 3.8.4
    
    def abstract(self, *expressions: List["Expression"], abstraction_kwargs={}) -> "Expression":
        # abstraction arity - (1) 3.8.5
        # prevent arity cross of single expression
        new_arity = ArityArrow(ArityCross(*[e.arity for e in expressions]) if len(expressions) > 1 else expressions[0].arity, self.arity)
        return self.default_abstraction_class()(self, expressions, new_arity, **abstraction_kwargs) 
    
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
        new_expr = self.copy()
                
        gbe_generator = general_bind_expression_generator()
        
        def search_func(wr1): 
            # find abstraction and walk parent swaping abstracted expression
            # with generic expression
            
            if type(wr1.expr.parent) is AbstractionExpression:
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
        new_expr.walk(search_func)

        return new_expr
        
    def beta_reduction(self):
        """beta-reduce expression, ie apply to abstraction
        """
        # todo: test arity
        new_expr = self.copy()
        if isinstance(new_expr, ApplicationExpression) and isinstance(new_expr.base, AbstractionExpression):
            new_expr = new_expr.base.base
            for i, expr in enumerate(self.base.children): # abstractions
                new_expr = new_expr.substitute(expr, self.children[i])
        return new_expr

class Symbol(metaclass=ExpressionMetaClass, expression_base_class=Expression):
    __default_arity__ = A0
    
    def __init__(self, str_repr=None, arity=None, canonical=None, latex_repr=None):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExpression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is canonical or not. defaults to None (ie unknown).
        """
        super().__init__()
        self.str_repr = str_repr
        self.latex_repr = latex_repr if latex_repr is not None else str_repr
        self._arity = arity if arity is not None else self.__class__.__default_arity__
        self.canonical = canonical

    @alias_render_typestring
    def render_typestring(self, renderer):  # @UnusedVariable
        return self.str_repr
    
    @alias_render_latex
    def render_latex(self, renderer):  # @UnusedVariable
        return self.latex_repr
    
    def render_graphtool(self, renderer):
        graph = renderer.new_graph()
        base_vertex = graph.add_vertex()
        graph.gp["basevertex"] = base_vertex
        graph.vp["label"][base_vertex] = self.str_repr
        return graph
    
    def equals(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        return isinstance(other, self.__class__) and self.str_repr == other.str_repr and self.arity == other.arity
    
    def walk(self, func, **options):  # @UnusedVariable
        pass
    
    def substitute(self, from_expr, to_expr: "Expression") -> "Expression":
        return to_expr.copy()  if self == from_expr else self.copy() #  exact substitution - (2) 2.4

class ExpressionCombination(metaclass=ExpressionMetaClass, expression_base_class=Expression):    
    def __init__(self, *expressions: List[Expression]):
        """Combines list into comma-concatenated expression.
        Args:
            expressions (List[Expression]): list of expressions
        """
        self.children = list(deepcopy(expressions))
        self._arity = ArityCross(*[e.arity for e in expressions]) # (1) 3.8.6
        self._str_repr_alias = None
        self._latex_repr_alias = None
         
    def equals(self, other):
        """Overload == and compare expressions.
        Following (1) 3.9.
        """
        # combinations are dealt with separately
        if self.children and other.children:
            return all([t == o and t.arity == o.arity for t,o in zip(self.children, other.children)])

    def __getitem__(self, index):
        """Overload [] for selection"""
        return self.select(index)
         
    def select(self, i: int) -> Expression:
        """Selects indexed subexpression from expression.
        Args:
            i (int): integer subexpression
        """
        new_expr = self.children[i].copy()
        new_expr._arity = self.arity.args[i] # (1) 3.8.7
        return new_expr

    def walk(self, func, **options):  # @UnusedVariable
        raise ToBeImplemented("Walk not implemented for this class yet")

    def substitute(self, from_expr, to_expr: "Expression") -> "Expression":
        raise ToBeImplemented("Substitute not implemented for this class yet")
    
    @alias_render_typestring     
    def render_typestring(self, renderer):
        return ", ".join([renderer.render(e) for e in self.children])
    
    @alias_render_latex     
    def render_latex(self, renderer):
        return ", ".join([renderer.render(e) for e in self.children])

class BaseWithChildrenExpression(metaclass=ExpressionMetaClass, expression_base_class=Expression):
    # todo: perhaps utilize ExpressionCombination for children here?
    def __init__(self, base: "ExpressionBase", expressions: List["ExpressionBase"], arity=None):
        super().__init__()
        self.base = base.copy()
        self.children = list(deepcopy(expressions))
        for e in self.children: e.parent = self 
        self._arity = arity.copy() if arity is not None else self.__class__.__default_arity__

    def __getitem__(self, index):
        """Overload [] for selection"""
        return self.select(index)
         
    def select(self, i: int) -> Expression:
        """Selects indexed subexpression from expression.
        Args:
            i (int): integer subexpression
        """
        if self.children is not None:
            new_expr = self.children[i].copy()
            new_expr._arity = self.arity.args[i] # (1) 3.8.7
            return new_expr
    
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
            return to_expr.copy() # (2) 2.4
        
        # check from_expr is free in this expression
        if self.contains_bind(to_expr):
            raise ToBeImplemented("Cannot yet substitute bound expression")
        
        new_expr = self.copy()
        new_expr.base = new_expr.base.substitute(from_expr, to_expr) # (2) 2.4
        
        for i, child in enumerate(new_expr.children): # (2) 2.4
            new_expr.children[i] = child.substitute(from_expr, to_expr)
        
        return new_expr

class ApplicationExpression(metaclass=ExpressionMetaClass, expression_base_class=BaseWithChildrenExpression, default_application_class=True):
    @alias_render_typestring
    def render_typestring(self, renderer):  # @UnusedVariable
        return "%s%s%s%s" % (self.base.render_typestring(renderer), APPLY_LEFT_BRACKET, ", ".join([e.render_typestring(renderer) for e in self.children]), APPLY_RIGHT_BRACKET)
    
    @alias_render_latex
    def render_latex(self, renderer):  # @UnusedVariable
        return "%s%s%s%s" % (self.base.render_latex(renderer), APPLY_LEFT_BRACKET, ", ".join([e.render_latex(renderer) for e in self.children]), APPLY_RIGHT_BRACKET)
    
    def render_graphtool(self, renderer):  # @UnusedVariable
        from graph_tool.generation import graph_union
        
        graph = self.base.render_graphtool(renderer)
        base_vertex = graph.gp["basevertex"]
        
        for e in self.children:
            subgraph = e.render_graphtool(renderer)
            
            subgraph_placeholder_vertex = graph.add_vertex()
            graph.add_edge(base_vertex, subgraph_placeholder_vertex)

            intersection_map = subgraph.new_vertex_property("int")
            for v in subgraph.vertices():
                intersection_map[v] = -1
            intersection_map[subgraph.vertex(base_vertex)] = subgraph_placeholder_vertex
             
            graph, combined_props = graph_union(graph, subgraph,
                   props=[(graph.vp["label"], subgraph.vp["label"])],
                   intersection=intersection_map)
            graph.vp["label"] = combined_props[0]
            graph.gp["basevertex"] = graph.new_graph_property("int", base_vertex)

        return graph
    
class AbstractionExpression(metaclass=ExpressionMetaClass, expression_base_class=BaseWithChildrenExpression, default_abstraction_class=True):
    @alias_render_typestring
    def render_typestring(self, renderer):  # @UnusedVariable
        return "%s%s%s%s" % (ABSTRACT_LEFT_BRACKET, ", ".join([e.render_typestring(renderer) for e in self.children]), ABSTRACT_RIGHT_BRACKET, self.base.render_typestring(renderer))
    
    @alias_render_latex
    def render_latex(self, renderer):  # @UnusedVariable
        return r"λ%s%s%s.%s" % (ABSTRACT_LEFT_BRACKET, ", ".join([e.render_latex(renderer) for e in self.children]), ABSTRACT_RIGHT_BRACKET, self.base.render_latex_wrap_parenthesis(renderer))

    def render_graphtool(self, renderer):  # @UnusedVariable
        from graph_tool.generation import graph_union
        
        graph = self.base.render_graphtool(renderer)
        base_vertex = graph.gp["basevertex"]
        
        lambda_vertex = graph.add_vertex()
        graph.gp["basevertex"] = lambda_vertex
        graph.vp["label"][lambda_vertex] = "λ"
        graph.add_edge(base_vertex, lambda_vertex)
        
        for e in self.children:
            subgraph = e.render_graphtool(renderer)
             
            subgraph_placeholder_vertex = graph.add_vertex()
            graph.add_edge(lambda_vertex, subgraph_placeholder_vertex)
            
            intersection_map = subgraph.new_vertex_property("int") 
            for v in subgraph.vertices():
                intersection_map[v] = -1
            intersection_map[subgraph.vertex(subgraph.gp["basevertex"])] = subgraph_placeholder_vertex
             
            graph, combined_props = graph_union(graph, subgraph,
                   props=[(graph.vp["label"], subgraph.vp["label"])],
                   intersection=intersection_map)
            graph.vp["label"] = combined_props[0]
            graph.gp["basevertex"] = graph.new_graph_property("int", lambda_vertex)
            
        return graph



    
