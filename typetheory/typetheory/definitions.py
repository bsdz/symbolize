from copy import deepcopy

from .expression import Expression
from .arity import ArityArrow, ArityCross, A0
from .render.latex import LatexRenderer

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

class BinaryInfixExpression(Expression):
    default_arity = ArityArrow(ArityCross(A0,A0),A0)
    
    def render_latex_baserepr(self):
        return None
    
    def render_latex_applications(self):
        return (" %s " % self.latexrepr).join([LatexRenderer(e).render() for e in self.applications])
    
plus = BinaryInfixExpression('+')
mult = BinaryInfixExpression('*', latexrepr=r'\mult')
in_ = BinaryInfixExpression('in', latexrepr=r'\in')

class IntegralExpression(Expression):
    default_arity = ArityArrow(ArityCross(ArityArrow(A0,A0),A0,A0),A0)
    
    def render_latex_baserepr(self):
        return None
    
    def render_latex_applications(self):
        integrand, limit_min, limit_max = self.applications
        dummy_var = integrand.abstractions[0]
        integrand_excl_abstraction = deepcopy(integrand)
        integrand_excl_abstraction.abstractions = None
        return "%s_{%s=%s}^{%s}{%s}" % tuple([self.latexrepr] + [LatexRenderer(e).render() for e in (dummy_var, limit_min, limit_max, integrand_excl_abstraction)])
    
integral = IntegralExpression('Integral', latexrepr=r'\int')
sum_ = IntegralExpression('Sum', latexrepr=r'\sum')
product = IntegralExpression('Product', latexrepr=r'\prod')

class NaturalNumber(BinaryInfixExpression):
    def __init__(self, member_label):
        super(NaturalNumber, self).__init__('in', latexrepr=r'\in')
        new_obj = self.apply(Expression(member_label), N)
        self.__dict__.update(new_obj.__dict__)
