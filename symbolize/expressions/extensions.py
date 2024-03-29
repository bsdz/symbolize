"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from collections import defaultdict

from .expression import (
    Symbol,
    ApplicationExpression,
    alias_render_latex,
    alias_render_unicode,
)
from .arity import ArityArrow, ArityCross, A0


class BinaryInfixExpression(ApplicationExpression):
    @alias_render_latex
    def render_latex(self, renderer):
        return "%s %s %s" % (
            self.children[0].render_latex_wrap_parenthesis(renderer),
            self.base.render_latex(renderer),
            self.children[1].render_latex_wrap_parenthesis(renderer),
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        return "%s %s %s" % (
            self.children[0].render_unicode_wrap_parenthesis(renderer),
            self.base.render_unicode(renderer),
            self.children[1].render_unicode_wrap_parenthesis(renderer),
        )


class BinaryInfixSymbol(Symbol):
    __arity__ = ArityArrow(ArityCross(A0, A0), A0)
    __application_class__ = BinaryInfixExpression


class LambdaExpression(ApplicationExpression):
    @alias_render_latex
    def render_latex(self, renderer):
        return "%s(%s)(%s)" % tuple(
            [
                e.render_latex(renderer)
                for e in [self.base]
                + self.children[0].children
                + [self.children[0].base]
            ]
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        return "%s(%s)(%s)" % tuple(
            [
                e.render_unicode(renderer)
                for e in [self.base]
                + self.children[0].children
                + [self.children[0].base]
            ]
        )


class LambdaSymbol(Symbol):
    __arity__ = ArityArrow(ArityArrow(A0, A0), A0)
    __application_class__ = LambdaExpression


class IntegralExpression(ApplicationExpression):
    @alias_render_latex
    def render_latex(self, renderer):
        integrand, limit_min, limit_max = self.children
        dummy_var = integrand.children[0]
        return "%s_{%s=%s}^{%s}{%s}" % tuple(
            [
                e.render_latex(renderer)
                for e in (self.base, dummy_var, limit_min, limit_max, integrand.base)
            ]
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        integrand, limit_min, limit_max = self.children
        dummy_var = integrand.children[0]
        return "%s%s (%s=%s..%s)" % tuple(
            [
                e.render_unicode(renderer)
                for e in (self.base, integrand.base, dummy_var, limit_min, limit_max)
            ]
        )


class IntegralSymbol(Symbol):
    __arity__ = ArityArrow(ArityCross(ArityArrow(A0, A0), A0, A0), A0)
    __application_class__ = IntegralExpression


class InclusionExclusionExpression(ApplicationExpression):
    """We store into the latex render a dict of tuples grouping the
    inclusions/exclusions so they may be rendered at end of final
    expression.
    """

    @alias_render_latex
    def render_latex(self, renderer):
        if not hasattr(renderer, "_inclusion_exclusion_groups"):
            renderer._inclusion_exclusion_groups = defaultdict(set)

            def _render_latex_postfix(renderer):
                if renderer._inclusion_exclusion_groups:
                    return "[%s]" % ", ".join(
                        [
                            "%s %s %s"
                            % (
                                ", ".join(
                                    [e.render_latex(renderer) for e in mem_expr_set]
                                ),
                                oper_collect[0].render_latex(renderer),
                                oper_collect[1].render_latex(renderer),
                            )
                            for oper_collect, mem_expr_set in renderer._inclusion_exclusion_groups.items()
                        ]
                    )

            renderer.postfix_hooks.append(_render_latex_postfix)

        renderer._inclusion_exclusion_groups[(self.base, self.children[1])].add(
            self.children[0]
        )
        return self.children[0].render_latex(renderer)

    @alias_render_unicode
    def render_unicode(self, renderer):
        if not hasattr(renderer, "_inclusion_exclusion_groups"):
            renderer._inclusion_exclusion_groups = defaultdict(set)

            def _render_unicode_postfix(renderer):
                if renderer._inclusion_exclusion_groups:
                    return "[%s]" % ", ".join(
                        [
                            "%s %s %s"
                            % (
                                ", ".join(
                                    [e.render_unicode(renderer) for e in mem_expr_set]
                                ),
                                oper_collect[0].render_unicode(renderer),
                                oper_collect[1].render_unicode(renderer),
                            )
                            for oper_collect, mem_expr_set in renderer._inclusion_exclusion_groups.items()
                        ]
                    )

            renderer.postfix_hooks.append(_render_unicode_postfix)

        renderer._inclusion_exclusion_groups[(self.base, self.children[1])].add(
            self.children[0]
        )
        return self.children[0].render_unicode(renderer)


class InclusionExclusionSymbol(Symbol):
    __arity__ = ArityArrow(ArityCross(A0, A0), A0)
    __application_class__ = InclusionExclusionExpression


class LogicQuantificationExpression(ApplicationExpression):
    @alias_render_latex
    def render_latex(self, renderer):
        return "%s{%s}.%s" % (
            self.base.render_latex(renderer),
            self.children[0].render_latex_wrap_parenthesis(renderer),
            self.children[1].render_latex_wrap_parenthesis(renderer),
        )

    @alias_render_unicode
    def render_unicode(self, renderer):
        return "%s%s.%s" % (
            self.base.render_unicode(renderer),
            self.children[0].render_unicode_wrap_parenthesis(renderer),
            self.children[1].render_unicode_wrap_parenthesis(renderer),
        )


class LogicQuantificationSymbol(Symbol):
    __application_class__ = LogicQuantificationExpression
