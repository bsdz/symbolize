"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from typing import List
from copy import deepcopy
from warnings import warn
from itertools import count
from functools import wraps
from enum import IntFlag

from .arity import A0, ArityArrow, ArityCross, ArityExpression
from .render.typestring import TypeStringRenderer, TypeStringRendererMixin
from .render.latex import LatexRenderer, LatexRendererMixin
from .render.graph import GraphToolRenderer, GraphToolRendererMixin
from .render.unicode import UnicodeRenderer, UnicodeRendererMixin


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


def alias_render_unicode(f):
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self._unicode_repr_alias is not None:
            return self._unicode_repr_alias
        return f(self, *args, **kwargs)

    return wrapper


class ExpressionWalkResult:
    __slots__ = ["expr", "obj", "index"]

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
    # we have an infinite collection of variables
    prefix = "__gbe_"
    for i in count(start=0, step=1):
        yield Symbol("%s%s" % (prefix, i))


class FoundExpressionException(Exception):
    pass


class ExpressionException(Exception):
    pass


APPLY_LEFT_BRACKET = "("
APPLY_RIGHT_BRACKET = ")"
ABSTRACT_LEFT_BRACKET = "("
ABSTRACT_RIGHT_BRACKET = ")"
SUBSTITUTE_LEFT_BRACKET = "["
SUBSTITUTE_RIGHT_BRACKET = "]"


class ExpressionClassType(IntFlag):
    ABSTRACTION = 1
    APPLICATION = 2
    SUBSTITUTION = 4


class ExpressionMetaClass(type):
    """This meta class injects as class attributes the
    various abstraction, application and substitution
    classes used for abstract(), apply() and substitute()
    methods."""

    def __new__(cls, clsname, bases, dct, **kwargs):
        new_type = type.__new__(cls, clsname, bases, dct)

        expression_class_type = kwargs.pop(
            "expression_class_type", ExpressionClassType(0)
        )
        if ExpressionClassType.ABSTRACTION in expression_class_type:
            cls.__abstraction_class__ = new_type
        if ExpressionClassType.APPLICATION in expression_class_type:
            cls.__application_class__ = new_type
        if ExpressionClassType.SUBSTITUTION in expression_class_type:
            cls.__substitution_class__ = new_type

        return new_type


class Expression(
    TypeStringRendererMixin,
    LatexRendererMixin,
    UnicodeRendererMixin,
    GraphToolRendererMixin,
    metaclass=ExpressionMetaClass,
):
    def repr_function(self):
        return self.repr_typestring()

    def jupyter_repr_latex_function(self):
        return "$$%s$$" % self.repr_latex()

    def jupyter_repr_html_function(self):
        return None
        # return "<pre>%s</pre>" % self.repr_unicode()

    def __init__(self, *args, **kwargs):
        self.parent = None
        self._arity = None
        self._str_repr_alias = None
        self._latex_repr_alias = None
        self._unicode_repr_alias = None
        self._assume_contains = kwargs.pop("assume_contains", [])

    def __repr__(self):
        return Expression.repr_function(self)

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
        return Expression.jupyter_repr_latex_function(self)

    def _repr_html_(self):
        """For Jupyter/IPython"""
        return Expression.jupyter_repr_html_function(self)

    def repr_typestring(self):
        return TypeStringRenderer().render(self)

    def repr_latex(self):
        return LatexRenderer().render(self)

    def repr_unicode(self):
        return UnicodeRenderer().render(self)

    def repr_graphtool(self):
        return GraphToolRenderer().render(self)

    @property
    def arity(self):
        return self._arity

    @arity.setter
    def arity(self, value):
        warn(
            "Setting arity outside object initialisation does not pass through to base expression"
        )
        self._arity = value

    def alias(self, str_repr, latex_repr=None):
        new_alias = self.copy()
        new_alias._str_repr_alias = str_repr
        new_alias._unicode_repr_alias = str_repr
        new_alias._latex_repr_alias = str_repr if latex_repr is None else latex_repr
        return new_alias

    def list_copies(self):
        # TODO: is this useful?
        print([k for k, v in globals().items() if v is self])

    def copy(self):
        """A deep copy of this expression"""
        return deepcopy(self)

    def apply(
        self, *expressions: "Expression", check_arity=True, target_arity=None, **kwargs,
    ) -> "Expression":
        """ [BN] 3.8.4
        """
        if check_arity:  # TODO: do we need this?
            if not isinstance(self.arity, ArityArrow):
                raise ExpressionException(
                    "Cannot apply when arity has no arrow: %s" % self.arity
                )
            if len(expressions) == 1 and expressions[0].arity != self.arity.lhs:
                raise ExpressionException(
                    "Cannot apply when arity arrow lhs does not match child arity: %s ≠ %s"
                    % (self.arity.lhs, expressions[0].arity)
                )
            if (
                len(expressions) > 1
                and isinstance(self.arity.lhs, ArityCross)
                and not all(
                    [e.arity == a for e, a in zip(expressions, self.arity.lhs.args)]
                )
            ):
                raise ExpressionException(
                    "Cannot apply when arity arrow lhs does not match child arity: %s ≠ %s"
                    % (self.arity.lhs, ArityCross(*[e.arity for e in expressions]))
                )
        else:
            warn("Skipping arity check on apply")

        if self.arity.rhs == A0:
            if target_arity is None:
                target_arity = self.arity.rhs
            return self.__class__.__application_class__(
                self, expressions, target_arity, **kwargs
            )
        else:
            raise ExpressionException(
                f"Do no support apply when rhs arity is {self.arity.rhs}"
            )

    def abstract(
        self, *expressions: "Expression", abstraction_kwargs={}
    ) -> "Expression":
        """ [BN] 3.8.5
            prevent arity cross of single expression
        """
        new_arity = ArityArrow(
            ArityCross(*[e.arity for e in expressions])
            if len(expressions) > 1
            else expressions[0].arity,
            self.arity,
        )
        return self.__class__.__abstraction_class__(
            self, expressions, new_arity, **abstraction_kwargs
        )

    def substitute(self, old, new, substitution_kwargs={}):
        return self.__class__.__substitution_class__(
            self, old, new, **substitution_kwargs
        )

    def walk(self, func, **options):
        """walks the expression, calling func on each sub part.
        func can return False to terminate the walk.

        abstract method.
        """
        raise NotImplementedError(
            f"Walk not implemented for this class yet: {type(self)}"
        )

    def equals(self, other):
        """Compares expression with another.

        abstract method.
        """
        raise NotImplementedError(
            f"Equals not implemented for this class yet: {type(self)}"
        )

    def replace(self, from_expr, to_expr: "Expression") -> "Expression":
        """ Replaces all occurrences of from_expr with to_expr.

        abstract method.
        """
        raise NotImplementedError(
            f"Replace not implemented for this class yet: {type(self)}"
        )

    def contains(self, expr):
        if self == expr or expr in self._assume_contains:
            return True
        else:

            def search_func(wr):
                if wr.expr == expr or expr in wr.expr._assume_contains:
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

    def contains_free(self, expr):
        return self.contains(expr) and not self.contains_bind(expr)

    def general_bind_form(self):
        """replaces all bound variables with general ordinal expression.
        """
        new_expr = self.copy()

        gbe_generator = general_bind_expression_generator()

        def search_func(wr1):
            # find abstraction and walk parent swapping abstracted expression
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
        # TODO: test arity
        new_expr = self.copy()
        if isinstance(new_expr, ApplicationExpression) and isinstance(
            new_expr.base, AbstractionExpression
        ):
            new_expr = new_expr.base.base
            for i, expr in enumerate(self.base.children):  # abstractions
                new_expr = new_expr.replace(expr, self.children[i])
        return new_expr


class Symbol(Expression, metaclass=ExpressionMetaClass):
    __arity__: ArityExpression = A0

    def __init__(
        self,
        str_repr=None,
        arity=None,
        canonical=None,
        latex_repr=None,
        *args,
        **kwargs,
    ):
        """
        Args:
            baserepr (str): the string representation of the expression
            arity (ArityExpression): the arity of the expression. defaults to single/saturated.
            canonical (bool): expression is canonical or not. defaults to None (ie unknown).
        """
        super().__init__(*args, **kwargs)
        self.str_repr = str_repr
        self.latex_repr = latex_repr if latex_repr is not None else str_repr
        self._arity = arity if arity is not None else self.__class__.__arity__
        self.canonical = canonical

    @alias_render_typestring
    def render_typestring(self, renderer):
        return self.str_repr

    @alias_render_latex
    def render_latex(self, renderer):
        return self.latex_repr

    @alias_render_unicode
    def render_unicode(self, renderer):
        return self.str_repr

    def render_graphtool(self, renderer):
        graph = renderer.new_graph()
        base_vertex = graph.add_vertex()
        graph.gp["basevertex"] = base_vertex
        graph.vp["label"][base_vertex] = self.str_repr
        return graph

    def equals(self, other):
        """Overload == and compare expressions.
        Following [BN] 3.9.
        """
        return (
            isinstance(other, self.__class__)
            and self.str_repr == other.str_repr
            and self.arity == other.arity
        )

    def walk(self, func, **options):
        pass

    def replace(self, from_expr, to_expr: "Expression") -> "Expression":
        # substitute assumptions
        if from_expr in self._assume_contains:
            self._assume_contains[self._assume_contains.index(from_expr)] = to_expr

        return (
            to_expr.copy() if self == from_expr else self.copy()
        )  # exact substitution - [ST] 2.4


class ExpressionCombination(
    Expression, metaclass=ExpressionMetaClass,
):
    def __init__(self, *expressions: Expression):
        """Combines list into comma-concatenated expression.
        Args:
            expressions (List[Expression]): list of expressions
        """
        self.children = list(deepcopy(expressions))
        self._arity = ArityCross(*[e.arity for e in expressions])  # [BN] 3.8.6
        self._str_repr_alias = None
        self._latex_repr_alias = None
        self._unicode_repr_alias = None

    def equals(self, other):
        """Overload == and compare expressions.
        Following [BN] 3.9.
        """
        # combinations are dealt with separately
        if self.children and other.children:
            return all(
                [
                    t == o and t.arity == o.arity
                    for t, o in zip(self.children, other.children)
                ]
            )

    def __getitem__(self, index):
        """Overload [] for selection"""
        return self.select(index)

    def select(self, i: int) -> Expression:
        """Selects indexed subexpression from expression.
        Args:
            i (int): integer subexpression
        """
        new_expr = self.children[i].copy()
        new_expr._arity = self.arity.args[i]  # [BN] 3.8.7
        return new_expr

    def walk(self, func, **options):
        raise NotImplementedError(f"Walk not implemented for this class yet: {type(self)}")

    def replace(self, from_expr, to_expr: Expression) -> Expression:
        raise NotImplementedError("Substitute not implemented for this class yet")

    @alias_render_typestring
    def render_typestring(self, renderer):
        return ", ".join([renderer.render(e) for e in self.children])

    @alias_render_latex
    def render_latex(self, renderer):
        return ", ".join([renderer.render(e) for e in self.children])

    @alias_render_unicode
    def render_unicode(self, renderer):
        return ", ".join([renderer.render(e) for e in self.children])


class SubstitutionExpression(
    Expression,
    metaclass=ExpressionMetaClass,
    expression_class_type=ExpressionClassType.SUBSTITUTION,
):
    __arity__: ArityExpression = A0

    def __init__(
        self,
        original: "Expression",
        old: "Expression",
        new: "Expression",
        arity=None,
        *args,
        **kwargs,
    ):
        """Substitutes source for target in original expression.

        Args:
            original Expression: original expression.
            old Expression: expression to substitute.
            new Expression: expression to insert.
        """
        super().__init__(*args, **kwargs)
        self.original = original.copy()
        self.old = old.copy()
        self.new = new.copy()

        # use base arity (TODO: is this correct?)
        self._arity = (
            self.original.copy()
            if arity is not None
            else self.__class__.__arity__
        )

    def equals(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self.original != other.original:
            return False

        if self.old and other.old:
            if not (self.old == other.old and self.old.arity == other.old.arity):
                return False

        if self.new and other.new:
            if not (self.new == other.new and self.new.arity == other.new.arity):
                return False
        return True

    def contains(self, expr):
        if self.old == expr:
            return False

        return self.original.replace(self.old, self.new).contains(expr)

    def walk(self, func, **options):
        func(ExpressionWalkResult(self.original, obj=self))
        self.original.walk(func, **options)

        func(ExpressionWalkResult(self.old, obj=self))
        self.old.walk(func, **options)

        func(ExpressionWalkResult(self.new, obj=self))
        self.new.walk(func, **options)

    #     def __getattr__(self, attr):
    #         """ any other expression we can pass through to original
    #         """
    #         return getattr(self.original.replace(self.old, self.new), attr)

    @alias_render_typestring
    def render_typestring(self, renderer):
        return "%s%s%s:=%s%s" % (
            self.original.render_typestring(renderer),
            SUBSTITUTE_LEFT_BRACKET,
            self.old.render_typestring(renderer),
            self.new.render_typestring(renderer),
            SUBSTITUTE_RIGHT_BRACKET,
        )

    @alias_render_latex
    def render_latex(self, renderer):
        # NOTE: mathjax does not support \coloneqq
        return r"%s%s%s \mathrel{\vcenter{:}}= %s%s" % (
            self.original.render_latex(renderer),
            SUBSTITUTE_LEFT_BRACKET,
            self.old.render_latex(renderer),
            self.new.render_latex(renderer),
            SUBSTITUTE_RIGHT_BRACKET,
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        return r"%s%s%s≔%s%s" % (
            self.original.render_unicode(renderer),
            SUBSTITUTE_LEFT_BRACKET,
            self.old.render_unicode(renderer),
            self.new.render_unicode(renderer),
            SUBSTITUTE_RIGHT_BRACKET,
        )


class BaseWithChildrenExpression(
    Expression, metaclass=ExpressionMetaClass,
):
    __arity__: ArityExpression = A0

    # TODO: perhaps utilize ExpressionCombination for children here?
    def __init__(
        self,
        base: "Expression",
        expressions: List["Expression"],
        arity=None,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.base = base.copy()
        self.children = list(deepcopy(expressions))
        for e in self.children:
            e.parent = self
        self._arity = (
            arity.copy() if arity is not None else self.__class__.__arity__
        )

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
            new_expr._arity = self.arity.args[i]  # [BN] 3.8.7
            return new_expr

    def equals(self, other):
        """Following [BN] 3.9.
        """
        # TODO: convert to general bind form before comparison (make optional?)
        if not isinstance(other, self.__class__):
            return False

        if self.base != other.base:
            return False

        if self.children and other.children:  # TODO: do we need to check arity here?
            if not all(
                [
                    t == o and t.arity == o.arity
                    for t, o in zip(self.children, other.children)
                ]
            ):
                return False
        return True

    def walk(self, func, **options):
        func(ExpressionWalkResult(self.base, obj=self))
        self.base.walk(func, **options)
        for i, expr in enumerate(self.children):
            func(ExpressionWalkResult(expr, obj=self.children, index=i))
            expr.walk(func, **options)

    def replace(self, from_expr, to_expr: "Expression") -> "Expression":

        if self == from_expr:  # exact substitution
            return to_expr.copy()  # [ST] 2.4

        # check from_expr is free in this expression
        if self.contains_bind(to_expr):
            raise NotImplementedError("Cannot yet substitute bound expression")

        new_expr = self.copy()
        new_expr.base = new_expr.base.replace(from_expr, to_expr)  # [ST] 2.4

        for i, child in enumerate(new_expr.children):  # [ST] 2.4
            new_expr.children[i] = child.replace(from_expr, to_expr)

        # substitute assumptions
        if from_expr in self._assume_contains:
            self._assume_contains[self._assume_contains.index(from_expr)] = to_expr

        return new_expr


class ApplicationExpression(
    BaseWithChildrenExpression,
    metaclass=ExpressionMetaClass,
    expression_class_type=ExpressionClassType.APPLICATION,
):
    @alias_render_typestring
    def render_typestring(self, renderer):
        return "%s%s%s%s" % (
            self.base.render_typestring(renderer),
            APPLY_LEFT_BRACKET,
            ", ".join([e.render_typestring(renderer) for e in self.children]),
            APPLY_RIGHT_BRACKET,
        )

    @alias_render_latex
    def render_latex(self, renderer):
        return "%s%s%s%s" % (
            self.base.render_latex(renderer),
            APPLY_LEFT_BRACKET,
            ", ".join([e.render_latex(renderer) for e in self.children]),
            APPLY_RIGHT_BRACKET,
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        return "%s%s%s%s" % (
            self.base.render_unicode(renderer),
            APPLY_LEFT_BRACKET,
            ", ".join([e.render_unicode(renderer) for e in self.children]),
            APPLY_RIGHT_BRACKET,
        )

    def render_graphtool(self, renderer):
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

            graph, combined_props = graph_union(
                graph,
                subgraph,
                props=[(graph.vp["label"], subgraph.vp["label"])],
                intersection=intersection_map,
            )
            graph.vp["label"] = combined_props[0]
            graph.gp["basevertex"] = graph.new_graph_property("int", base_vertex)

        return graph


class AbstractionExpression(
    BaseWithChildrenExpression,
    metaclass=ExpressionMetaClass,
    expression_class_type=ExpressionClassType.ABSTRACTION,
):
    @alias_render_typestring
    def render_typestring(self, renderer):
        return "%s%s%s%s" % (
            ABSTRACT_LEFT_BRACKET,
            ", ".join([e.render_typestring(renderer) for e in self.children]),
            ABSTRACT_RIGHT_BRACKET,
            self.base.render_typestring(renderer),
        )

    @alias_render_latex
    def render_latex(self, renderer):
        return r"\lambda{}%s%s%s.%s" % (
            ABSTRACT_LEFT_BRACKET,
            ", ".join([e.render_latex(renderer) for e in self.children]),
            ABSTRACT_RIGHT_BRACKET,
            self.base.render_latex_wrap_parenthesis(renderer),
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        return r"λ%s%s%s.%s" % (
            ABSTRACT_LEFT_BRACKET,
            ", ".join([e.render_unicode(renderer) for e in self.children]),
            ABSTRACT_RIGHT_BRACKET,
            self.base.render_unicode_wrap_parenthesis(renderer),
        )

    def render_graphtool(self, renderer):
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
            intersection_map[
                subgraph.vertex(subgraph.gp["basevertex"])
            ] = subgraph_placeholder_vertex

            graph, combined_props = graph_union(
                graph,
                subgraph,
                props=[(graph.vp["label"], subgraph.vp["label"])],
                intersection=intersection_map,
            )
            graph.vp["label"] = combined_props[0]
            graph.gp["basevertex"] = graph.new_graph_property("int", lambda_vertex)

        return graph
