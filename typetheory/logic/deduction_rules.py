from ..definitions.operators import pair
from ..definitions.functions import fst, snd, inl, inr
from ..definitions.logic import and_, implies, or_

from .proposition import get_proposition_class

# conjunctions
#
def conjunction_introduction(a_,b_):
    new_expr = and_(a_.proposition_expr, b_.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = pair(a_.proof_expr, b_.proof_expr)
    return cls(proof_expr)

def conjunction_elimination_1(a_):
    if a_.proposition_expr.base != and_:
        raise Exception("Cannot eliminate without conjunction")
    new_expr = a_.proposition_expr.children[0]
    cls = get_proposition_class(new_expr)
    proof_expr = fst(a_.proof_expr)
    return cls(proof_expr)

def conjunction_elimination_2(a_):
    if a_.proposition_expr.base != and_:
        raise Exception("Cannot eliminate without conjunction")
    new_expr = a_.proposition_expr.children[1]
    cls = get_proposition_class(new_expr)
    proof_expr = snd(a_.proof_expr)
    return cls(proof_expr)

# implications
#  
def implication_introduction(a_, b_):
    new_expr = implies(a_.proposition_expr, b_.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = b_.proof_expr.abstract(a_.proof_expr)
    return cls(proof_expr)

def implication_elimation(a_, b_):
    if a_.proposition_expr.base != implies:
        raise Exception("Cannot eliminate without implication")
    new_expr = a_.proposition_expr.children[1]
    cls = get_proposition_class(new_expr)
    proof_expr = a_.proof_expr.apply(b_.proof_expr)
    return cls(proof_expr)

# disjunctions
#
def disjunction_introduction_1(a_, B_):
    # todo check B_ is not instance
    new_expr = or_(a_.proposition_expr, B_.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = inl(a_.proof_expr)
    return cls(proof_expr)

def disjunction_introduction_2(a_, B_):
    # todo check B is not instance
    new_expr = or_(B_.proposition_expr, a_.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = inr(a_.proof_expr)
    return cls(proof_expr)

