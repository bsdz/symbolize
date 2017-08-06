from collections import defaultdict
from copy import deepcopy

from .expression import Expression
from .arity import ArityArrow, ArityCross, A0
from .render.latex import LatexRendererExpressionMixin

class BinaryInfixExpression(Expression, LatexRendererExpressionMixin):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None if self.applications else self.latexrepr # without applications should just show symbol
    
    def render_latex_applications(self, renderer):
        return "%s %s %s" % (renderer.render(self.applications[0]), self.latexrepr, renderer.render(self.applications[1]))
    
class InclusionExclusionExpression(Expression, LatexRendererExpressionMixin):
    """
    We store into the latex render a dict of tuples grouping the
    inclusions/exclusions so they may be rendered at end of final
    expression.
    """
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None
    
    def render_latex_applications(self, renderer):
        if not hasattr(renderer, '_inclusion_exclusion_groups'):
            renderer._inclusion_exclusion_groups = defaultdict(set)
            
            def _render_latex_postfix(renderer):
                if renderer._inclusion_exclusion_groups:
                    return "[%s]" % ", ".join(["%s %s %s" % (", ".join([renderer.render(e) for e in mem_expr_set]), 
                                      oper_collect[0], renderer.render(oper_collect[1]))
                     for oper_collect, mem_expr_set in renderer._inclusion_exclusion_groups.items()])
            
            renderer.postfix_hooks.append(_render_latex_postfix)
        
        renderer._inclusion_exclusion_groups[(self.latexrepr, self.applications[1])].add(self.applications[0])
        return renderer.render(self.applications[0])
    
    def render_latex_parenthesize_applications(self, renderer):  # @UnusedVariable
        return False


class IntegralExpression(Expression, LatexRendererExpressionMixin):
    default_arity = ArityArrow(ArityCross(ArityArrow(A0,A0),A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None
    
    def render_latex_applications(self, renderer):
        integrand, limit_min, limit_max = self.applications
        dummy_var = integrand.abstractions[0]
        integrand_excl_abstraction = deepcopy(integrand)
        integrand_excl_abstraction.abstractions = None
        return "%s_{%s=%s}^{%s}{%s}" % tuple([self.latexrepr] + [renderer.render(e) for e in (dummy_var, limit_min, limit_max, integrand_excl_abstraction)])
 
 
class LogicQuantificationExpression(Expression, LatexRendererExpressionMixin):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None if self.applications else self.latexrepr # without applications should just show symbol
    
    def render_latex_applications(self, renderer):
        return "%s(%s).%s" % (self.latexrepr, renderer.render(self.applications[0]), renderer.render(self.applications[1]))
 