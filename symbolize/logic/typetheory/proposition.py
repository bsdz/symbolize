from ...expressions import ExpressionMetaClass, Expression, Symbol, BaseWithChildrenExpression,\
        A0, ArityArrow, ArityCross,\
        BinaryInfixSymbol, BinaryInfixExpression,\
        LogicQuantificationSymbol, LogicQuantificationExpression
        
from .proof import ProofSymbol, ProofExpressionCombination

def general_proof_label_generator():
    from itertools import count
    prefix = "p_"
    for i in count(start=0, step=1): # we have an infinite collection of variables
        yield '%s%s' % (prefix, i)

proof_label_generator = general_proof_label_generator()

class PropositionExpressionMetaClass(ExpressionMetaClass):
    pass

class PropositionExpression(Expression, metaclass=PropositionExpressionMetaClass):
    def __init__(self, *args, **kwargs):
        self.proof_default_arity = kwargs.pop("proof_default_arity", None)
        self.proof_function = kwargs.pop("proof_function", None)
        self.assumption_contains_free = kwargs.pop("assumption_contains_free", [])
        super().__init__()
        
    def get_proof(self, name):
        if self.proof_function is not None:
            new_proof = self.proof_function(self).alias(name)
        else:
            new_proof = ProofSymbol(str_repr=name, proposition_type=self, arity=self.proof_default_arity)
        return new_proof
    
    def contains_free(self, expr):
        """Allow us to override base"""
        if expr in self.assumption_contains_free:
            return True
        else:
            return super().contains_free(expr)
        
class PropositionSymbol(Symbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    """*@DynamicAttrs*"""
    pass

class PropositionBaseWithChildrenExpression(BaseWithChildrenExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    pass

class PropositionBinaryInfixExpression(BinaryInfixExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionBaseWithChildrenExpression):
    pass
        
class PropositionBinaryInfixSymbol(BinaryInfixSymbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    __default_application_class__ = PropositionBinaryInfixExpression
        
    def apply(self, *expressions):
        return super().apply(*expressions, application_kwargs={
            "proof_default_arity": self.proof_default_arity,
            "proof_function": self.proof_function
        })
        
class PropositionLogicQuantificationExpression(LogicQuantificationExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionBaseWithChildrenExpression):
    pass
        
class PropositionLogicQuantificationSymbol(LogicQuantificationSymbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    __default_application_class__ = PropositionLogicQuantificationExpression
        
    def apply(self, *expressions):
        return super().apply(*expressions, application_kwargs={
            "proof_default_arity": self.proof_default_arity,
            "proof_function": self.proof_function
        })


def and_pf(prop_type):
    p1 = prop_type.children[0].get_proof(next(proof_label_generator))
    p2 = prop_type.children[1].get_proof(next(proof_label_generator))
    return ProofExpressionCombination(p1, p2)

def implies_pf(prop_type):
    p1 = prop_type.children[0].get_proof(next(proof_label_generator))
    p2 = prop_type.children[1].get_proof(next(proof_label_generator))
    return p2.abstract(p1)

def or_pf(prop_type):
    from .proof import inl, inr
    p1 = prop_type.children[0].get_proof(next(proof_label_generator))
    p2 = prop_type.children[1].get_proof(next(proof_label_generator))
    # todo - can be inl or inr with indicator of which proof has evidence
    return inl(p1, p2.proposition_type)

# definitions
#
and_ = PropositionBinaryInfixSymbol('∧', latex_repr=r'\land', proof_default_arity=ArityCross(A0,A0), proof_function=and_pf)
or_ = PropositionBinaryInfixSymbol('∨', latex_repr=r'\lor', proof_default_arity=ArityCross(A0,A0), proof_function=or_pf)
implies = PropositionBinaryInfixSymbol('⟹', latex_repr=r'\Rightarrow', proof_default_arity=ArityArrow(A0,A0), proof_function=implies_pf)

forall = PropositionLogicQuantificationSymbol('∀', latex_repr=r'\forall')

#then = PropositionBinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
#iff = PropositionBinaryInfixSymbol('⟺', latex_repr=r'\iff')

not_ = PropositionSymbol('¬', arity=ArityArrow(A0,A0), latex_repr=r'\neg')
#exists = LogicQuantificationSymbol('∃', latex_repr=r'\exists')

