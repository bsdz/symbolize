'''
Created on 9 Sep 2017

@author: blair
'''

from ...expressions import ExpressionMetaClass, Expression, Symbol,\
        BaseWithChildrenExpression, ApplicationExpression, AbstractionExpression,\
        ExpressionCombination,\
        A0, ArityArrow, ArityCross
        

class ProofExpressionMetaClass(ExpressionMetaClass):
    pass

class ProofExpression(Expression, metaclass=ProofExpressionMetaClass):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def repr_latex(self):
        from symbolize.expressions.render.latex import LatexRenderer
        if self.proposition_type is None:
            return LatexRenderer().render(self)
        else:
            return "%s : %s" % (LatexRenderer().render(self), LatexRenderer().render(self.proposition_type))
        
    def apply(self, *expressions, **kwargs):
        new_prop_type = self.proposition_function(self, expressions)
        return super().apply(*expressions, application_kwargs={"proposition_type":new_prop_type}, **kwargs)

    def abstract(self, *expressions):
        from .proposition import implies
        # todo: check proof doesn't have binds otherwise forall-introduction
        new_prop_type = implies(expressions[0].proposition_type, self.proposition_type)
        return super().abstract(*expressions, abstraction_kwargs={"proposition_type":new_prop_type})
  
class ProofSymbol(Symbol, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    def __init__(self, *args, **kwargs):
        self.proposition_function = kwargs.pop("proposition_function", lambda s,e: e[0].proposition_type)
        self.proposition_type = kwargs.pop("proposition_type", None)
        Symbol.__init__(self, *args, **kwargs)
        
class ProofExpressionCombination(ExpressionCombination, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    def __init__(self, *args, **kwargs):
        from .proposition import and_
        # check only two proofs provided
        proposition_type = and_(args[0].proposition_type, args[1].proposition_type)
        self.proposition_type = proposition_type
        ExpressionCombination.__init__(self, *args, **kwargs)

class ProofBaseWithChildrenExpression(BaseWithChildrenExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    pass

class ProofApplicationExpression(ApplicationExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofBaseWithChildrenExpression, default_application_class=True):
    def __init__(self, *args, **kwargs):
        self.proposition_type = kwargs.pop("proposition_type", None)
        ApplicationExpression.__init__(self, *args, **kwargs)
        
class ProofAbstractionExpression(AbstractionExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofBaseWithChildrenExpression, default_abstraction_class=True):
    def __init__(self, *args, **kwargs):
        self.proposition_function = lambda s,e: s.proposition_type.children[1]
        self.proposition_type = kwargs.pop("proposition_type", None)
        AbstractionExpression.__init__(self, *args, **kwargs)       


# definitions
#
def fst_prop_function(self, expr):
    return expr[0].proposition_type.children[0]

fst = ProofSymbol('fst', ArityArrow(ArityCross(A0, A0), A0), proposition_function=fst_prop_function)
snd = ProofSymbol('snd', ArityArrow(ArityCross(A0, A0), A0), proposition_function=lambda s,e: e[0].proposition_type.children[1])

# we adjust inl/inr to accept 2nd argument of proposition type to inject. 
def inl_prop_function(self, expr):
    from .proposition import or_
    return or_(expr[0].proposition_type, expr[1])

def inr_prop_function(self, expr):
    from .proposition import or_
    return or_(expr[1], expr[0].proposition_type)
    
inl = ProofSymbol('inl', ArityArrow(ArityCross(A0, A0), A0), proposition_function=inl_prop_function)
inr = ProofSymbol('inr', ArityArrow(ArityCross(A0, A0), A0), proposition_function=inr_prop_function)

def cases_prop_function(self, expr):
    # todo: check inputs
    return expr[1].proposition_type.children[1]

cases = ProofSymbol('cases', ArityArrow(ArityCross(A0,ArityArrow(A0,A0),ArityArrow(A0,A0)), A0), proposition_function=cases_prop_function)
