from copy import deepcopy
from collections import defaultdict

from .expression import Expression
from .arity import ArityArrow, ArityCross, A0

x = Expression('x')
y = Expression('y')
z = Expression('z')

a = Expression('a')
b = Expression('b')
c = Expression('c')

sin = Expression('sin', arity=ArityArrow(A0,A0))

# primitive constants (appendix A1)
# N
zero = Expression('0', A0, True)
succ = Expression('succ', ArityArrow(A0,A0), True)
natrec = Expression('natrec', ArityArrow(ArityCross(A0,A0,ArityArrow(ArityCross(A0,A0),A0)),A0), False)
# List(A)
nil = Expression('nil', A0, True)
cons = Expression('cons', ArityArrow(A0,A0), True)
listrec = Expression('listrec', ArityArrow(ArityCross(A0,A0,ArityArrow(ArityCross(A0,A0,A0),A0)),A0), False)
# A -> B, Product(A, B)
lambda_ = Expression('lambda', ArityArrow(ArityArrow(A0,A0),A0), True)
apply = Expression('apply', ArityArrow(ArityCross(A0,A0),A0), False)
funsplit = Expression('funsplit', ArityArrow(ArityCross(A0,ArityArrow(A0,A0)),A0), False)

# sets
N = Expression('N', latexrepr=r'\mathbb{N}')
R = Expression('R', latexrepr=r'\mathbb{R}')

class NAryInfixExpression(Expression):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None
    
    def render_latex_applications(self, renderer):
        return (" %s " % self.latexrepr).join([renderer.render(e) for e in self.applications])

class BinaryInfixExpression(Expression):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None
    
    def render_latex_applications(self, renderer):
        return "%s %s %s" % (renderer.render(self.applications[0]), self.latexrepr, renderer.render(self.applications[1]))
    
plus = BinaryInfixExpression('+')
mult = BinaryInfixExpression('*', latexrepr=r'\mult')

class InclusionExclusionExpression(Expression):
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
    

    
in_ = InclusionExclusionExpression('in', latexrepr=r'\in')

class IntegralExpression(Expression):
    default_arity = ArityArrow(ArityCross(ArityArrow(A0,A0),A0,A0),A0)
    
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return None
    
    def render_latex_applications(self, renderer):
        integrand, limit_min, limit_max = self.applications
        dummy_var = integrand.abstractions[0]
        integrand_excl_abstraction = deepcopy(integrand)
        integrand_excl_abstraction.abstractions = None
        return "%s_{%s=%s}^{%s}{%s}" % tuple([self.latexrepr] + [renderer.render(e) for e in (dummy_var, limit_min, limit_max, integrand_excl_abstraction)])
    
integral = IntegralExpression('Integral', latexrepr=r'\int')
sum_ = IntegralExpression('Sum', latexrepr=r'\sum')
product = IntegralExpression('Product', latexrepr=r'\prod')


class NaturalNumber(InclusionExclusionExpression):
    def __init__(self, member_label):
        super(NaturalNumber, self).__init__('in', latexrepr=r'\in')
        new_obj = self.apply(Expression(member_label), N)
        self.__dict__.update(new_obj.__dict__)
