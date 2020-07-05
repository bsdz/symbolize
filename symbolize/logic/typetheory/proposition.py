"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ...expressions import (
    ExpressionMetaClass,
    Expression,
    Symbol,
    BaseWithChildrenExpression,
    SubstitutionExpression,
    A0,
    ArityArrow,
    ArityCross,
    BinaryInfixSymbol,
    BinaryInfixExpression,
    LogicQuantificationSymbol,
    LogicQuantificationExpression,
)

from .proof import ProofSymbol, ProofExpressionCombination
from ...utility import ToBeImplemented


def general_proof_label_generator():
    from itertools import count

    prefix = "p_"
    for i in count(start=0, step=1):  # we have an infinite collection of variables
        yield "%s%s" % (prefix, i)


proof_label_generator = general_proof_label_generator()


class PropositionExpressionMetaClass(ExpressionMetaClass):
    pass


class PropositionSubstitutionExpression(SubstitutionExpression):
    def get_proof(self, name, **kwargs):
        proof = self.original.get_proof(name, **kwargs)
        proof.proposition_type = self  # todo: copy?
        return proof


class PropositionExpression(Expression, metaclass=PropositionExpressionMetaClass):

    __substitution_class__ = PropositionSubstitutionExpression

    def get_proof(self, name, **kwargs):
        raise ToBeImplemented("Need to implement")


class PropositionSymbol(
    Symbol,
    PropositionExpression,
    metaclass=PropositionExpressionMetaClass,
):
    """*@DynamicAttrs*"""

    def get_proof(self, name, **kwargs):
        return ProofSymbol(str_repr=name, proposition_type=self)


class PropositionBaseWithChildrenExpression(
    BaseWithChildrenExpression,
    PropositionExpression,
    metaclass=PropositionExpressionMetaClass,
):
    pass


class PropositionBinaryInfixExpression(
    BinaryInfixExpression,
    PropositionBaseWithChildrenExpression,
    metaclass=PropositionExpressionMetaClass,
):
    pass


class PropositionBinaryInfixSymbol(
    BinaryInfixSymbol,
    PropositionExpression,
    metaclass=PropositionExpressionMetaClass,
):
    __application_class__ = PropositionBinaryInfixExpression


class PropositionLogicQuantificationExpression(
    LogicQuantificationExpression,
    PropositionBaseWithChildrenExpression,
    metaclass=PropositionExpressionMetaClass,
):
    pass


class PropositionLogicQuantificationSymbol(
    LogicQuantificationSymbol,
    PropositionExpression,
    metaclass=PropositionExpressionMetaClass,
):
    __application_class__ = PropositionLogicQuantificationExpression


# definitions
#
class AndPropositionExpression(PropositionBinaryInfixExpression):
    """ [ST] p78
    """

    def get_proof(self, name, **kwargs):
        p1 = self.children[0].get_proof(next(proof_label_generator), **kwargs)
        p2 = self.children[1].get_proof(next(proof_label_generator), **kwargs)
        return ProofExpressionCombination(p1, p2).alias(name)


class AndPropositionSymbol(PropositionBinaryInfixSymbol):
    __application_class__ = AndPropositionExpression


class OrPropositionExpression(PropositionBinaryInfixExpression):
    """ [ST] p81
    """

    def get_proof(self, name, **kwargs):
        from .proof import inl  # , inr

        p1 = self.children[0].get_proof(next(proof_label_generator), **kwargs)
        p2 = self.children[1].get_proof(next(proof_label_generator), **kwargs)
        # todo - can be inl or inr with indicator of which proof has evidence
        return inl(p1, inject_proposition=p2.proposition_type).alias(name)


class OrPropositionSymbol(PropositionBinaryInfixSymbol):
    __application_class__ = OrPropositionExpression


class ImpliesPropositionExpression(PropositionBinaryInfixExpression):
    """ [ST] p79
    """

    def get_proof(self, name, **kwargs):
        p1 = self.children[0].get_proof(next(proof_label_generator), **kwargs)
        p2 = self.children[1].get_proof(next(proof_label_generator), **kwargs)
        return p2.abstract(p1).alias(name)


class ImpliesPropositionSymbol(PropositionBinaryInfixSymbol):
    __application_class__ = ImpliesPropositionExpression


class ForallPropositionExpression(PropositionLogicQuantificationExpression):
    """ [ST] p89
    """

    def get_proof(self, name, **kwargs):
        p1 = self.children[0]
        p2 = self.children[1].get_proof(next(proof_label_generator), **kwargs)
        return p2.abstract(p1).alias(name)


class ForallPropositionSymbol(PropositionLogicQuantificationSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0, ArityArrow(A0, A0)), A0)
    __application_class__ = ForallPropositionExpression


class ExistsPropositionExpression(PropositionLogicQuantificationExpression):
    """ [ST] p91
    """

    def get_proof(self, name, **kwargs):
        p1 = self.children[0]
        p2 = self.children[1].get_proof(next(proof_label_generator), **kwargs)
        return ProofExpressionCombination(p1, p2).alias(name)


class ExistsPropositionSymbol(PropositionLogicQuantificationSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)  # todo: is this correct?
    __application_class__ = ExistsPropositionExpression


and_ = AndPropositionSymbol("∧", latex_repr=r"\land")
or_ = OrPropositionSymbol("∨", latex_repr=r"\lor")
implies = ImpliesPropositionSymbol("⟹", latex_repr=r"\Rightarrow")
forall = ForallPropositionSymbol("∀", latex_repr=r"\forall")
exists = ExistsPropositionSymbol("∃", latex_repr=r"\exists")

# then = PropositionBinaryInfixSymbol('⟸', latex_repr=r'\Leftarrow')
# iff = PropositionBinaryInfixSymbol('⟺', latex_repr=r'\iff')

not_ = PropositionSymbol("¬", arity=ArityArrow(A0, A0), latex_repr=r"\neg")
