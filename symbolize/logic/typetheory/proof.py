'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
from ...expressions import ExpressionMetaClass, Expression, Symbol,\
        BaseWithChildrenExpression, ApplicationExpression, AbstractionExpression,\
        ExpressionCombination,\
        A0, ArityArrow, ArityCross
from symbolize.utility import ToBeImplemented

class ProofExpressionMetaClass(ExpressionMetaClass):
    pass

class ProofExpression(Expression, metaclass=ProofExpressionMetaClass):
    def __init__(self, *args, **kwargs):
        self.proposition_type = kwargs.pop("proposition_type", None)
        super().__init__()
    
    def repr_typestring(self):
        from symbolize.expressions.render.typestring import TypeStringRenderer
        if self.proposition_type is None:
            return TypeStringRenderer().render(self)
        else:
            return "%s : %s" % (TypeStringRenderer().render(self), TypeStringRenderer().render(self.proposition_type))        
        
    def repr_latex(self):
        from symbolize.expressions.render.latex import LatexRenderer
        if self.proposition_type is None:
            return LatexRenderer().render(self)
        else:
            return "%s : %s" % (LatexRenderer().render(self), LatexRenderer().render(self.proposition_type))
        
    def repr_unicode(self):
        from symbolize.expressions.render.unicode import UnicodeRenderer
        if self.proposition_type is None:
            return UnicodeRenderer().render(self)
        else:
            return "%s : %s" % (UnicodeRenderer().render(self), UnicodeRenderer().render(self.proposition_type))
    
    def apply_proposition_type(self, expressions):
        raise ToBeImplemented("Need to implement a proposition type method!")
        
    def apply(self, *expressions, **kwargs):
        new_prop_type = self.apply_proposition_type(expressions)
        return super().apply(*expressions, application_kwargs={"proposition_type":new_prop_type}, **kwargs)

    def abstract(self, *expressions):
        from .proposition import implies, forall
        # check proof doesn't have expressions[0] free in self
        if self.proposition_type.contains_free(expressions[0]):
            new_prop_type = forall(expressions[0], self.proposition_type)
        else:
            new_prop_type = implies(expressions[0].proposition_type, self.proposition_type)
        return super().abstract(*expressions, abstraction_kwargs={"proposition_type":new_prop_type})
  
class ProofSymbol(Symbol, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):        
    pass
        
class ProofExpressionCombination(ExpressionCombination, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    def __init__(self, *args, **kwargs):
        from .proposition import and_
        # todo: check only two proofs provided
        self.proposition_type = and_(args[0].proposition_type, args[1].proposition_type)
        super().__init__(*args, **kwargs)

class ProofBaseWithChildrenExpression(BaseWithChildrenExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofExpression):
    pass

class ProofApplicationExpression(ApplicationExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofBaseWithChildrenExpression, default_application_class=True):
    pass
        
class ProofAbstractionExpression(AbstractionExpression, metaclass=ProofExpressionMetaClass, expression_base_class=ProofBaseWithChildrenExpression, default_abstraction_class=True):
    def apply_proposition_type(self, expressions):
        return self.proposition_type.children[1]

# definitions
# todo: check function inputs like .experimental.deduction_rules
#
class FstProofSymbol(ProofSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr):
        return expr[0].proposition_type.children[0]

class SndProofSymbol(ProofSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr):
        return expr[0].proposition_type.children[1]
    
class InlProofSymbol(ProofSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr):
        from .proposition import or_
        return or_(expr[0].proposition_type, expr[1])

class InrProofSymbol(ProofSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr):
        from .proposition import or_
        return or_(expr[1], expr[0].proposition_type)
    
class CasesProofSymbol(ProofSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0,ArityArrow(A0,A0),ArityArrow(A0,A0)), A0)
    def apply_proposition_type(self, expr):
        # todo: check inputs
        return expr[1].proposition_type.children[1]

class IfThenElseProofSymbol(ProofSymbol):
    __default_arity__ = ArityArrow(ArityCross(A0,ArityArrow(A0,A0),ArityArrow(A0,A0)), A0)
    def apply_proposition_type(self, expr):
        pass

fst = FstProofSymbol('fst')
snd = SndProofSymbol('snd')
inl = InlProofSymbol('inl')
inr = InrProofSymbol('inr')
cases = CasesProofSymbol('cases') 
ifthenelse = IfThenElseProofSymbol('ifthenelse')
