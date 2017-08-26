'''
Created on 3 Aug 2017

@author: bsdz
'''
from ..expressions import Symbol, Expression

class Proposition(object):
    # instances are proofs
    proposition_expr = None # class prop
    def __init__(self, baserepr, arity=None):
        self.proof_expr = baserepr if isinstance(baserepr, Expression) else Symbol(baserepr, arity)
        
    def repr_latex(self):
        return "%s : %s" % (self.proof_expr.repr_latex(), self.__class__.proposition_expr.repr_latex())
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.repr_latex()
        
def get_proposition_class(expr):
    """returns existing or new proposition class"""
    type_string = expr.repr_typestring()
    if type_string in globals():
        return globals()[type_string]
    else:
        return type(type_string, (Proposition,), { 
            "proposition_expr": expr
        })

