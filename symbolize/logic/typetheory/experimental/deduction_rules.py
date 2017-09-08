from ....expressions import ExpressionCombination

from ....definitions.operators import pair
from ....definitions.functions import fst, snd, inl, inr, cases
from ....definitions.logic import and_, implies, or_

from .proposition import get_proposition_class

# conjunctions
#
def conjunction_introduction(a,b): # (2) p79 4.4
    """Introduce conjunction.
    
    Args:
        a (Proposition): left hand proof.
        b (Proposition): right hand proof.
    """
    new_expr = and_(a.proposition_expr, b.proposition_expr)
    cls = get_proposition_class(new_expr)
    #proof_expr = pair(a.proof_expr, b.proof_expr)
    proof_expr = ExpressionCombination(a.proof_expr, b.proof_expr)
    return cls(proof_expr)

def conjunction_elimination_1(a): # (2) p79 4.4
    """Eliminate conjunction on right.
    
    Args:
        a (Proposition): proof containing conjunction.
    """
    if a.proposition_expr.base != and_:
        raise Exception("Cannot eliminate without conjunction")
    new_expr = a.proposition_expr.children[0]
    cls = get_proposition_class(new_expr)
    proof_expr = fst(a.proof_expr)
    return cls(proof_expr)

def conjunction_elimination_2(a): # (2) p79 4.4
    """Eliminate conjunction on left.
    
    Args:
        a (Proposition): proof containing conjunction.
    """
    if a.proposition_expr.base != and_:
        raise Exception("Cannot eliminate without conjunction")
    new_expr = a.proposition_expr.children[1]
    cls = get_proposition_class(new_expr)
    proof_expr = snd(a.proof_expr)
    return cls(proof_expr)

# implications
#  
def implication_introduction(a, b): # (2) p79 4.4
    """Introduce implication.
    
    Args:
        a (Proposition): left hand proof.
        b (Proposition): right hand proof.
    """
    new_expr = implies(a.proposition_expr, b.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = b.proof_expr.abstract(a.proof_expr)
    return cls(proof_expr)

def implication_elimation(a, b):  # (2) p80 4.4
    """Eliminate implication.
    
    Args:
        a (Proposition): left hand proof.
        b (Proposition): right hand proof.
    """
    if a.proposition_expr.base != implies:
        raise Exception("Cannot eliminate without implication")
    new_expr = a.proposition_expr.children[1]
    cls = get_proposition_class(new_expr)
    proof_expr = a.proof_expr.apply(b.proof_expr)
    return cls(proof_expr)

# disjunctions
#
def disjunction_introduction_1(a, B): # (2) p81 4.4
    """Introduce disjunction on left.
    
    Args:
        a (Proposition): proof.
        B (PropositionType): proposition.
    """
    if not isinstance(B, type):
        raise Exception("Need proposition type to introduce disjunct")
    new_expr = or_(a.proposition_expr, B.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = inl(a.proof_expr)
    return cls(proof_expr)

def disjunction_introduction_2(a, B): # (2) p80 4.4
    """Introduce disjunction on right.
    
    Args:
        a (Proposition): proof.
        B (PropositionType): proposition.
    """
    if not isinstance(B, type):
        raise Exception("Need proposition type to introduce disjunct")
    new_expr = or_(B.proposition_expr, a.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = inr(a.proof_expr)
    return cls(proof_expr)

def disjunction_elimination(a, b, c):  # (2) p80 4.4
    """Eliminate implication.
    
    Args:
        a (Proposition): proof requiring elimination.
        b (Proposition): 1st implication proof deducing C from a.
        c (Proposition): 2nd implication proof deducing C from a.
    """
    if a.proposition_expr.base != or_:
        raise Exception("Cannot eliminate without disjunction")
    if b.proposition_expr.base != implies or c.proposition_expr.base != implies:
        raise Exception("Cannot eliminate disjunction without two implications")
    if b.proposition_expr.children[1] != c.proposition_expr.children[1]:
        raise Exception("Cannot eliminate if both implications do not have same consequence")
    new_expr = b.proposition_expr.children[1]
    cls = get_proposition_class(new_expr)
    proof_expr = cases(a.proof_expr, b.proof_expr, c.proof_expr)
    return cls(proof_expr)



