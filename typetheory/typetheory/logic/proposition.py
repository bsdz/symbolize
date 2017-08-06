'''
Created on 3 Aug 2017

@author: bsdz
'''
from ..expressions import Expression
from ..definitions.operators import pair
from ..definitions.functions import fst, snd
from ..definitions.logic import and_, implies

class Proposition(object):
    # instances are proofs
    proposition_expr = None # class prop
    def __init__(self, baserepr, arity=None):
        self.proof_expr = baserepr if isinstance(baserepr, Expression) else Expression(baserepr, arity)
        
    def render_latex(self):
        return "%s : %s" % (self.proof_expr.render_latex(), self.__class__.proposition_expr.render_latex())
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.render_latex()
        
def get_proposition_class(expr):
    """returns existing or new proposition class"""
    type_string = expr.render_type_string()
    if type_string in globals():
        return globals()[type_string]
    else:
        return type(type_string, (Proposition,), { 
            "proposition_expr": expr
        })

def conjunction_introduction(a_,b_):
    new_expr = and_(a_.proposition_expr, b_.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = pair(a_.proof_expr, b_.proof_expr)
    return cls(proof_expr)

def conjunction_elimination_1(a_):
    if a_.proposition_expr.baserepr != "and":
        raise Exception("Cannot eliminate without conjunction")
    new_expr = a_.proposition_expr.applications[0]
    cls = get_proposition_class(new_expr)
    proof_expr = fst(a_.proof_expr)
    return cls(proof_expr)

def conjunction_elimination_2(a_):
    if a_.proposition_expr.baserepr != "and":
        raise Exception("Cannot eliminate without conjunction")
    new_expr = a_.proposition_expr.applications[1]
    cls = get_proposition_class(new_expr)
    proof_expr = snd(a_.proof_expr)
    return cls(proof_expr)

  
def implication_introduction(a_, b_):
    new_expr = implies(a_.proposition_expr, b_.proposition_expr)
    cls = get_proposition_class(new_expr)
    proof_expr = b_.proof_expr.abstract(a_.proof_expr)
    return cls(proof_expr)

def implication_elimation(a_, b_):
    if a_.proposition_expr.baserepr != "implies":
        raise Exception("Cannot eliminate without implication")
    new_expr = a_.proposition_expr.applications[1]
    cls = get_proposition_class(new_expr)
    proof_expr = a_.proof_expr.apply(b_.proof_expr)
    return cls(proof_expr)
  