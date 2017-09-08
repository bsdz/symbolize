from ...expressions import Symbol, ApplicationExpression, A0, ArityArrow, ArityCross, BinaryInfixSymbol, BinaryInfixExpression, ExpressionCombination

# mixins
#
class PropositionMixin(object):
    def __init__(self, proof_default_arity):
        self.proof_default_arity = proof_default_arity

    def get_proof(self, name):
        return Proof(str_repr=name, proposition_type=self, arity=self.proof_default_arity)

class ProofMixin(object):
    def __init__(self, proposition_type):
        self.proposition_type = proposition_type
        if self.proposition_type is None:
            raise Exception("need prop type")
        
    def repr_latex(self):
        from symbolize.expressions.render.latex import LatexRenderer
        return "%s : %s" % (LatexRenderer().render(self), LatexRenderer().render(self.proposition_type))

    @property
    def is_proof(self):
        return True

# prop + proof
#
class Proposition(PropositionMixin, Symbol):
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proof_default_arity = kwargs.pop("proof_default_arity", None))
        Symbol.__init__(self, *args, **kwargs)

    def default_application_class(self):
        return PropositionApplicationExpression
class PropositionApplicationExpression(ApplicationExpression, PropositionMixin):  pass

class Proof(ProofMixin, Symbol):
    def __init__(self, *args, **kwargs):
        ProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        Symbol.__init__(self, *args, **kwargs)

    
class PropositionBinaryInfixSymbol(BinaryInfixSymbol, PropositionMixin):
    def apply(self, *expressions, proof_default_arity=None):
        return BinaryInfixSymbol.apply(self, *expressions, application_kwargs={"proof_default_arity":proof_default_arity})
    def default_application_class(self):
        return PropositionBinaryInfixExpression

class PropositionBinaryInfixExpression(BinaryInfixExpression, PropositionMixin):
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proof_default_arity = kwargs.pop("proof_default_arity", None))
        BinaryInfixExpression.__init__(self, *args, **kwargs)

class ProofCombination(ProofMixin, ExpressionCombination):
    def __init__(self, *args, **kwargs):
        # check only two proofs provided
        proposition_type = and_(args[0].proposition_type, args[1].proposition_type)
        ProofMixin.__init__(self, proposition_type = proposition_type)
        ExpressionCombination.__init__(self, *args, **kwargs)

class ProofFunction(Symbol):
    def __init__(self, *args, **kwargs):
        self.proposition_function = kwargs.pop("proposition_function", None)
        Symbol.__init__(self, *args, **kwargs)

    def apply(self, *expressions):
        new_prop_type = self.proposition_function(expressions)
        return Symbol.apply(self, *expressions, application_kwargs={"proposition_type":new_prop_type})

    def default_application_class(self):
        return ProofFunctionExpression

class ProofFunctionExpression(ProofMixin, ApplicationExpression):
    def __init__(self, *args, **kwargs):
        ProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        ApplicationExpression.__init__(self, *args, **kwargs)


and_ = PropositionBinaryInfixSymbol('∧', latex_repr=r'\land')
or_ = PropositionBinaryInfixSymbol('∨', latex_repr=r'\lor')
implies = PropositionBinaryInfixSymbol('⟹', latex_repr=r'\Rightarrow')
then = PropositionBinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
iff = PropositionBinaryInfixSymbol('⟺', latex_repr=r'\iff')

#not_ = Symbol('¬', arity=ArityArrow(A0,A0), latex_repr=r'\neg')
#forall = LogicQuantificationSymbol('∀', latex_repr=r'\forall')
#exists = LogicQuantificationSymbol('∃', latex_repr=r'\exists')


fst = ProofFunction('fst', ArityArrow(ArityCross(A0,A0),A0), proposition_function=lambda expr: expr[0].proposition_type.children[0])
snd = ProofFunction('snd', ArityArrow(ArityCross(A0,A0),A0), proposition_function=lambda expr: expr[0].proposition_type.children[1])
        

