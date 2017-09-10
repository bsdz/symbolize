from ...expressions import Symbol, ApplicationExpression,\
        A0, ArityArrow, ArityCross,\
        BinaryInfixSymbol, BinaryInfixExpression
        
from .proof import Proof

# mixins
#
class PropositionMixin(object):
    def __init__(self, proof_default_arity):
        self.proof_default_arity = proof_default_arity

    def get_proof(self, name):
        return Proof(str_repr=name, proposition_type=self, arity=self.proof_default_arity)



# proposition
#
class PropositionApplicationExpression(ApplicationExpression, PropositionMixin):  pass

class Proposition(Symbol, PropositionMixin):
    __default_application_class__ = PropositionApplicationExpression
    
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proof_default_arity = kwargs.pop("proof_default_arity", None))
        Symbol.__init__(self, *args, **kwargs)


class PropositionBinaryInfixExpression(BinaryInfixExpression, PropositionMixin):
    def __init__(self, *args, **kwargs):
        PropositionMixin.__init__(self, proof_default_arity = kwargs.pop("proof_default_arity", None))
        BinaryInfixExpression.__init__(self, *args, **kwargs)
  
class PropositionBinaryInfixSymbol(BinaryInfixSymbol):
    __default_application_class__ = PropositionBinaryInfixExpression
    
    def __init__(self, *args, **kwargs):
        self.proof_default_arity = kwargs.pop("proof_default_arity", None)
        super().__init__(*args, **kwargs)
        
    def apply(self, *expressions):
        return BinaryInfixSymbol.apply(self, *expressions, application_kwargs={"proof_default_arity":self.proof_default_arity})



# definitions
#
and_ = PropositionBinaryInfixSymbol('∧', latex_repr=r'\land', proof_default_arity=ArityCross(A0,A0))
or_ = PropositionBinaryInfixSymbol('∨', latex_repr=r'\lor')
implies = PropositionBinaryInfixSymbol('⟹', latex_repr=r'\Rightarrow', proof_default_arity=ArityArrow(A0,A0))

then = PropositionBinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
iff = PropositionBinaryInfixSymbol('⟺', latex_repr=r'\iff')

#not_ = Symbol('¬', arity=ArityArrow(A0,A0), latex_repr=r'\neg')
#forall = LogicQuantificationSymbol('∀', latex_repr=r'\forall')
#exists = LogicQuantificationSymbol('∃', latex_repr=r'\exists')



        

