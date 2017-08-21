from collections import defaultdict

from .expression import Symbol, ApplicationExpression
from .arity import ArityArrow, ArityCross, A0

class BinaryInfixExpression(ApplicationExpression):
    def render_latex(self, renderer):  # @UnusedVariable
        lhs = self.children[0].render_latex(renderer)
        if isinstance(self.children[0], ApplicationExpression):
            lhs = "(%s)" % lhs
        rhs = self.children[1].render_latex(renderer)
        if isinstance(self.children[1], ApplicationExpression):
            rhs = "(%s)" % rhs
        return "%s %s %s" % (lhs, self.base.render_latex(renderer), rhs)

class BinaryInfixSymbol(Symbol):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def default_application_class(self):
        return BinaryInfixExpression


class IntegralExpression(ApplicationExpression):
    def render_latex(self, renderer):  # @UnusedVariable
        integrand, limit_min, limit_max = self.children
        dummy_var = integrand.children[0]
        return "%s_{%s=%s}^{%s}{%s}" % tuple([e.render_latex(renderer) for e in (self.base, dummy_var, limit_min, limit_max, integrand.base)])
 
class IntegralSymbol(Symbol):
    default_arity = ArityArrow(ArityCross(ArityArrow(A0,A0),A0,A0),A0)
    
    def default_application_class(self):
        return IntegralExpression


class InclusionExclusionExpression(ApplicationExpression):
    def render_latex(self, renderer):
        if not hasattr(renderer, '_inclusion_exclusion_groups'):
            renderer._inclusion_exclusion_groups = defaultdict(set)
            
            def _render_latex_postfix(renderer):
                if renderer._inclusion_exclusion_groups:
                    return "[%s]" % ", ".join(["%s %s %s" % (", ".join([e.render_latex(renderer) for e in mem_expr_set]), 
                                      oper_collect[0].render_latex(renderer), oper_collect[1].render_latex(renderer))
                     for oper_collect, mem_expr_set in renderer._inclusion_exclusion_groups.items()])
            
            renderer.postfix_hooks.append(_render_latex_postfix)
        
        renderer._inclusion_exclusion_groups[(self.base, self.children[1])].add(self.children[0])
        return self.children[0].render_latex(renderer)
    
    def render_latex_parenthesize_applications(self, renderer):  # @UnusedVariable
        return False
 
class InclusionExclusionSymbol(Symbol):
    """
    We store into the latex render a dict of tuples grouping the
    inclusions/exclusions so they may be rendered at end of final
    expression.
    """
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def default_application_class(self):
        return InclusionExclusionExpression


class LogicQuantificationExpression(ApplicationExpression):
    def render_latex_applications(self, renderer):  # @UnusedVariable
        return "%s(%s).%s" % (self.latexrepr, self.children[0].render_latex(renderer), self.children[1].render_latex(renderer))
    
class LogicQuantificationSymbol(Symbol):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def default_application_class(self):
        return LogicQuantificationExpression
