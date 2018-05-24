'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

from ...expressions import ExpressionMetaClass, Expression, Symbol, BaseWithChildrenExpression,\
        A0, ArityArrow, ArityCross,\
        BinaryInfixSymbol, BinaryInfixExpression,\
        LogicQuantificationSymbol, LogicQuantificationExpression
        
from .proof import ProofSymbol, ProofExpressionCombination
from symbolize.utility import ToBeImplemented

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
        super().__init__(*args, **kwargs)
        
    def get_proof(self, name):
        raise ToBeImplemented("Need to implement")
    
    def contains_free(self, expr):
        """Allow us to override base"""
        return super().contains_free(expr)
        
    def apply(self, *expressions):
        return super().apply(*expressions, application_kwargs={})
        
class PropositionSymbol(Symbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    """*@DynamicAttrs*"""
    def get_proof(self, name):
        return ProofSymbol(str_repr=name, proposition_type=self)

class PropositionBaseWithChildrenExpression(BaseWithChildrenExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    pass

class PropositionBinaryInfixExpression(BinaryInfixExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionBaseWithChildrenExpression):
    pass
        
class PropositionBinaryInfixSymbol(BinaryInfixSymbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    __default_application_class__ = PropositionBinaryInfixExpression
        
class PropositionLogicQuantificationExpression(LogicQuantificationExpression, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionBaseWithChildrenExpression):
    pass
        
class PropositionLogicQuantificationSymbol(LogicQuantificationSymbol, metaclass=PropositionExpressionMetaClass, expression_base_class=PropositionExpression):
    __default_application_class__ = PropositionLogicQuantificationExpression
        

# definitions
#
class AndPropositionExpression(PropositionBinaryInfixExpression):
    """ [ST] p78
    """
    def get_proof(self, name):
        p1 = self.children[0].get_proof(next(proof_label_generator))
        p2 = self.children[1].get_proof(next(proof_label_generator))
        return ProofExpressionCombination(p1, p2).alias(name)
        
class AndPropositionSymbol(PropositionBinaryInfixSymbol):
    __default_application_class__ = AndPropositionExpression
    
class OrPropositionExpression(PropositionBinaryInfixExpression):
    """ [ST] p81
    """
    def get_proof(self, name):
        from .proof import inl, inr
        p1 = self.children[0].get_proof(next(proof_label_generator))
        p2 = self.children[1].get_proof(next(proof_label_generator))
        # todo - can be inl or inr with indicator of which proof has evidence
        return inl(p1, p2.proposition_type).alias(name)
        
class OrPropositionSymbol(PropositionBinaryInfixSymbol):
    __default_application_class__ = OrPropositionExpression
    
class ImpliesPropositionExpression(PropositionBinaryInfixExpression):
    """ [ST] p79
    """
    def get_proof(self, name):
        p1 = self.children[0].get_proof(next(proof_label_generator))
        p2 = self.children[1].get_proof(next(proof_label_generator))
        return p2.abstract(p1).alias(name)
        
class ImpliesPropositionSymbol(PropositionBinaryInfixSymbol):
    __default_application_class__ = ImpliesPropositionExpression
    
class ForallPropositionExpression(PropositionLogicQuantificationExpression):
    """ [ST] p89
    """
    def get_proof(self, name):
        p1 = self.children[0]
        p2 = self.children[1].get_proof(next(proof_label_generator))
        return p2.abstract(p1).alias(name)
        
class ForallPropositionSymbol(PropositionLogicQuantificationSymbol):
    __default_application_class__ = ForallPropositionExpression

class ExistsPropositionExpression(PropositionLogicQuantificationExpression):
    """ [ST] p91
    """
    def get_proof(self, name, exists_expression=None):
        p1 = self.children[0]
        p2 = self.children[1].get_proof(next(proof_label_generator))
        return ProofExpressionCombination(p1, p2, exists_expression=exists_expression).alias(name)
        
class ExistsPropositionSymbol(PropositionLogicQuantificationSymbol):
    __default_application_class__ = ExistsPropositionExpression

and_ = AndPropositionSymbol('∧', latex_repr=r'\land')
or_ = OrPropositionSymbol('∨', latex_repr=r'\lor')
implies = ImpliesPropositionSymbol('⟹', latex_repr=r'\Rightarrow')
forall = ForallPropositionSymbol('∀', latex_repr=r'\forall')
exists = ExistsPropositionSymbol('∃', latex_repr=r'\exists')

#then = PropositionBinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
#iff = PropositionBinaryInfixSymbol('⟺', latex_repr=r'\iff')

not_ = PropositionSymbol('¬', arity=ArityArrow(A0,A0), latex_repr=r'\neg')

