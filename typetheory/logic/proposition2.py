from ..expressions import *

class TTProofMixin(object):
    def __init__(self, proposition_type):
        self.proposition_type = proposition_type
        if self.proposition_type is None:
            raise Exception("need prop type")
        
    def repr_latex(self):
        from typetheory.expressions.render.latex import LatexRenderer
        return "%s : %s" % (LatexRenderer().render(self), LatexRenderer().render(self.proposition_type))

    @property
    def is_proof(self):
        return True
    

class TTProof(TTProofMixin, Symbol):
    def __init__(self, *args, **kwargs):
        TTProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        Symbol.__init__(self, *args, **kwargs)


class TTPropositionMixin(object):
    def get_proof(self, name):
        return TTProof(name, proposition_type=self)

    
class TTProposition(TTPropositionMixin, Symbol):
    def default_application_class(self):
        return TTPropositionApplicationExpression
class TTPropositionApplicationExpression(ApplicationExpression, TTPropositionMixin):  pass
        
    
class TTPropositionBinaryInfixSymbol(BinaryInfixSymbol, TTPropositionMixin):
    def default_application_class(self):
        return TTPropositionBinaryInfixExpression
class TTPropositionBinaryInfixExpression(BinaryInfixExpression, TTPropositionMixin):   pass


and_ = TTPropositionBinaryInfixSymbol('∧', latex_repr=r'\land')


class TTExpressionCombination(TTProofMixin,ExpressionCombination):
    def __init__(self, *args, **kwargs):
        # check only two proofs provided
        proposition_type = and_(args[0].proposition_type, args[1].proposition_type)
        TTProofMixin.__init__(self, proposition_type = proposition_type)
        ExpressionCombination.__init__(self, *args, **kwargs)



class TTFunction(Symbol):
    def __init__(self, *args, **kwargs):
        self.proposition_function = kwargs.pop("proposition_function", None)
        Symbol.__init__(self, *args, **kwargs)

    def apply(self, *expressions):
        res = Symbol.apply(self, *expressions)
        res.proposition_type = self.proposition_function(res)
        return res

    def default_application_class(self):
        return TTFunctionApplicationExpression

class TTFunctionApplicationExpression(TTProofMixin, ApplicationExpression):
    def __init__(self, *args, **kwargs):
        TTProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        ApplicationExpression.__init__(self, *args, **kwargs)


fst = TTFunction('fst', ArityArrow(ArityCross(A0,A0),A0), proposition_function=lambda expr: expr.children[0].proposition_type)

        
A = TTProposition('A')
B = TTProposition('B')
a = A.get_proof('a')
b = B.get_proof('b')
p = and_(A,B).get_proof('p')
TTExpressionCombination(a,b)
