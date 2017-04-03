# todo: convert to ArityExpression class
class ArityPlaceHolder(object):
    def __repr__(self):
        return "0"


A0 = ArityPlaceHolder() # convenience instance

def repr_arity_brackets(arity_expr):
    if arity_expr is A0:
        return repr(A0)
    else:
        return '(' + repr(arity_expr) + ')'
    
class ArityCross(object):
    def __init__(self, *args):
        self.args = args
        
    def __repr__(self):
        return " x ".join([repr_arity_brackets(i) for i in self.args])

class ArityArrow(object):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
        
    def __repr__(self):
        return "%s -> %s" % (repr_arity_brackets(self.lhs), repr_arity_brackets(self.rhs))