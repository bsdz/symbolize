
from itertools import count
from ...expressions import ExpressionMetaClass, Expression, Symbol, BaseWithChildrenExpression, ApplicationExpression,\
        A0, ArityArrow, ArityCross,\
        BinaryInfixSymbol, BinaryInfixExpression
        
from .proof import Proof, ProofCombination

def general_proof_label_generator():
    prefix = "p_"
    for i in count(start=0, step=1): # we have an infinite collection of variables
        yield '%s%s' % (prefix, i)

proof_label_generator = general_proof_label_generator()

class PropositionMixin(object):
    def __init__(self, proof_default_arity):
        self.proof_default_arity = proof_default_arity

class PropositionExpressionMetaClass(ExpressionMetaClass):
    pass

class PropositionExpression(Expression, metaclass=PropositionExpressionMetaClass):
    pass

class PropositionSymbol(PropositionMixin, Symbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proof_default_arity = kwargs.pop("proof_default_arity", None))
        Symbol.__init__(self, *args, **kwargs)

    def get_proof(self, name):
        return Proof(str_repr=name, proposition_type=self, arity=self.proof_default_arity)        

class PropositionBaseWithChildrenExpression(PropositionMixin, BaseWithChildrenExpression):
    pass

class PropositionApplicationExpression(ApplicationExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionBaseWithChildrenExpression, default_application_class=True):
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proposition_type = kwargs.pop("proof_default_arity", None))
        ApplicationExpression.__init__(self, *args, **kwargs)


Proposition = PropositionSymbol


class PropositionBinaryInfixExpression(BinaryInfixExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionBaseWithChildrenExpression):
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proof_default_arity = kwargs.pop("proof_default_arity", None))
        self.proof_function = kwargs.pop("proof_function", None)
        BinaryInfixExpression.__init__(self, *args, **kwargs)
        
    def get_proof(self, name):
        if self.proof_function is not None:
            new_proof = self.proof_function(self)
        else:
            new_proof = Proof(str_repr=name, proposition_type=self, arity=self.proof_default_arity)
        return new_proof
  
class PropositionBinaryInfixSymbol(BinaryInfixSymbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    __default_application_class__ = PropositionBinaryInfixExpression
    
    def __init__(self, *args, **kwargs):
        self.proof_default_arity = kwargs.pop("proof_default_arity", None)
        self.proof_function = kwargs.pop("proof_function", None)
        super().__init__(*args, **kwargs)
        
    def apply(self, *expressions):
        return BinaryInfixSymbol.apply(self, *expressions, application_kwargs={
            "proof_default_arity":self.proof_default_arity,
            "proof_function":self.proof_function
            })



def and_pf(prop_type):
    p1 = prop_type.children[0].get_proof(next(proof_label_generator))
    p2 = prop_type.children[1].get_proof(next(proof_label_generator))
    return ProofCombination(p1, p2)

def implies_pf(prop_type):
    p1 = prop_type.children[0].get_proof(next(proof_label_generator))
    p2 = prop_type.children[1].get_proof(next(proof_label_generator))
    return p2.abstract(p1)

# definitions
#
and_ = PropositionBinaryInfixSymbol('∧', latex_repr=r'\land', proof_default_arity=ArityCross(A0,A0), proof_function=and_pf)
or_ = PropositionBinaryInfixSymbol('∨', latex_repr=r'\lor')
implies = PropositionBinaryInfixSymbol('⟹', latex_repr=r'\Rightarrow', proof_default_arity=ArityArrow(A0,A0), proof_function=implies_pf)

then = PropositionBinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
iff = PropositionBinaryInfixSymbol('⟺', latex_repr=r'\iff')

#not_ = Symbol('¬', arity=ArityArrow(A0,A0), latex_repr=r'\neg')
#forall = LogicQuantificationSymbol('∀', latex_repr=r'\forall')
#exists = LogicQuantificationSymbol('∃', latex_repr=r'\exists')

