'''
Created on 9 Sep 2017

@author: blair
'''

from ...expressions import ExpressionMetaClass, Expression, Symbol,\
        BaseWithChildrenExpression, ApplicationExpression, AbstractionExpression,\
        ExpressionCombination,\
        A0, ArityArrow, ArityCross
        
class ProofMixin(object):
    def __init__(self, proposition_type):
        self.proposition_type = proposition_type
        if self.proposition_type is None:
            raise Exception("need prop type")
        
    def repr_latex(self):
        from symbolize.expressions.render.latex import LatexRenderer
        return "%s : %s" % (LatexRenderer().render(self), LatexRenderer().render(self.proposition_type))

class ProofExpressionMetaClass(ExpressionMetaClass):
    pass

class ProofExpression(Expression, metaclass=ProofExpressionMetaClass):
    pass
  
class ProofSymbol(ProofMixin, Symbol, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    def __init__(self, *args, **kwargs):
        ProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        Symbol.__init__(self, *args, **kwargs)
        
    def apply(self, *expressions):
        new_prop_type = expressions[0].proposition_type
        return Symbol.apply(self, *expressions, application_kwargs={"proposition_type":new_prop_type})

    def abstract(self, *expressions):
        from .proposition import implies
        # todo: check proof doesn't have binds otherwise forall-introduction
        new_prop_type = implies(expressions[0].proposition_type, self.proposition_type)
        return Symbol.abstract(self, *expressions, abstraction_kwargs={"proposition_type":new_prop_type})


class ProofExpressionCombination(ProofMixin, ExpressionCombination, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    def __init__(self, *args, **kwargs):
        from .proposition import and_
        # check only two proofs provided
        proposition_type = and_(args[0].proposition_type, args[1].proposition_type)
        ProofMixin.__init__(self, proposition_type = proposition_type)
        ExpressionCombination.__init__(self, *args, **kwargs)

class ProofBaseWithChildrenExpression(ProofMixin, BaseWithChildrenExpression):
    pass

class ProofApplicationExpression(ApplicationExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofBaseWithChildrenExpression, default_application_class=True):
    def __init__(self, *args, **kwargs):
        ProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        ApplicationExpression.__init__(self, *args, **kwargs)

class ProofAbstractionExpression(AbstractionExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofBaseWithChildrenExpression, default_abstraction_class=True):
    def __init__(self, *args, **kwargs):
        ProofMixin.__init__(self, proposition_type = kwargs.pop("proposition_type", None))
        ApplicationExpression.__init__(self, *args, **kwargs)       

    def apply(self, *expressions):
        new_prop_type = self.proposition_type.children[1]
        return AbstractionExpression.apply(self, *expressions, application_kwargs={"proposition_type":new_prop_type})

Proof = ProofSymbol    
ProofCombination = ProofExpressionCombination
    

# todo: integrate into ProofSymbol?
class ProofFunctionSymbol(ProofMixin, Symbol, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):    
    def __init__(self, *args, **kwargs):
        self.proposition_function = kwargs.pop("proposition_function", None)
        Symbol.__init__(self, *args, **kwargs)

    def apply(self, *expressions):
        new_prop_type = self.proposition_function(expressions)
        return Symbol.apply(self, *expressions, application_kwargs={"proposition_type":new_prop_type})
    
# definitions
#
fst = ProofFunctionSymbol('fst', ArityArrow(ArityCross(A0,A0),A0), proposition_function=lambda expr: expr[0].proposition_type.children[0])
snd = ProofFunctionSymbol('snd', ArityArrow(ArityCross(A0,A0),A0), proposition_function=lambda expr: expr[0].proposition_type.children[1])

