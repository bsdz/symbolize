from collections import defaultdict

from .expression import Symbol, ApplicationExpression
from .arity import ArityArrow, ArityCross, A0

class BinaryInfixExpression(ApplicationExpression):
    def render_latex(self, renderer):  # @UnusedVariable
        return "%s %s %s" % (self.children[0].render_latex_wrap_parenthesis(renderer), 
                             self.base.render_latex(renderer), 
                             self.children[1].render_latex_wrap_parenthesis(renderer))

class BinaryInfixSymbol(Symbol):
    __default_arity__ = ArityArrow(ArityCross(A0,A0),A0)
    __default_application_class__ = BinaryInfixExpression    


class LambdaExpression(ApplicationExpression):
    def render_latex(self, renderer):  # @UnusedVariable
        return "%s(%s)(%s)" % tuple([e.render_latex(renderer) for e in [self.base] + self.children[0].children + [self.children[0].base]])

class LambdaSymbol(Symbol):
    __default_arity__ = ArityArrow(ArityArrow(A0,A0),A0)
    __default_application_class__ = LambdaExpression


class IntegralExpression(ApplicationExpression):
    def render_latex(self, renderer):  # @UnusedVariable
        integrand, limit_min, limit_max = self.children
        dummy_var = integrand.children[0]
        return "%s_{%s=%s}^{%s}{%s}" % tuple([e.render_latex(renderer) for e in (self.base, dummy_var, limit_min, limit_max, integrand.base)])
 
class IntegralSymbol(Symbol):
    __default_arity__ = ArityArrow(ArityCross(ArityArrow(A0,A0),A0,A0),A0)
    __default_application_class__ = IntegralExpression


class InclusionExclusionExpression(ApplicationExpression):
    """We store into the latex render a dict of tuples grouping the
    inclusions/exclusions so they may be rendered at end of final
    expression.
    """
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
 
class InclusionExclusionSymbol(Symbol):
    __default_arity__ = ArityArrow(ArityCross(A0,A0),A0)
    __default_application_class__ = InclusionExclusionExpression


class LogicQuantificationExpression(ApplicationExpression):
    def render_latex(self, renderer):  # @UnusedVariable
        return "%s{%s}.%s" % (self.base.render_latex(renderer), 
                              self.children[0].render_latex_wrap_parenthesis(renderer), 
                              self.children[1].render_latex_wrap_parenthesis(renderer))    
   

class LogicQuantificationSymbol(Symbol):
    __default_arity__ = ArityArrow(ArityCross(A0,A0),A0)
    __default_application_class__ = LogicQuantificationExpression


    
