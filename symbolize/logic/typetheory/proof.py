'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
from warnings import warn
from ...expressions import ExpressionMetaClass, Expression, Symbol,\
        BaseWithChildrenExpression, ApplicationExpression, AbstractionExpression,\
        ExpressionCombination,\
        A0, ArityArrow, ArityCross
from symbolize.utility import ToBeImplemented

class PropositionException(Exception): pass

class ProofExpressionMetaClass(ExpressionMetaClass): pass

class ProofExpression(Expression, 
                      metaclass=ProofExpressionMetaClass):
    def __init__(self, *args, **kwargs):
        self.proposition_type = kwargs.pop("proposition_type", None)
        super().__init__()
    
    def repr_typestring(self):
        """ Overrides base method to support displaying proposition types. """
        from symbolize.expressions.render.typestring import TypeStringRenderer
        if self.proposition_type is None:
            return TypeStringRenderer().render(self)
        else:
            return "%s : %s" % (TypeStringRenderer().render(self), TypeStringRenderer().render(self.proposition_type))        
        
    def repr_latex(self):
        """ Overrides base method to support displaying proposition types. """
        from symbolize.expressions.render.latex import LatexRenderer
        if self.proposition_type is None:
            return LatexRenderer().render(self)
        else:
            return "%s : %s" % (LatexRenderer().render(self), LatexRenderer().render(self.proposition_type))
        
    def repr_unicode(self):
        """ Overrides base method to support displaying proposition types. """
        from symbolize.expressions.render.unicode import UnicodeRenderer
        if self.proposition_type is None:
            return UnicodeRenderer().render(self)
        else:
            return "%s : %s" % (UnicodeRenderer().render(self), UnicodeRenderer().render(self.proposition_type))
    
    def run(self):
        return self.compute()
    
    def compute(self, children=[]):
        return self
    
    def apply_proposition_type(self, expressions, **apply_proposition_type_kwargs):
        """ Provides the new proposition type generated after application. """
        raise ToBeImplemented("Need to implement a proposition type method!")
        
    def apply(self, *expressions, **kwargs):
        """ [ST] p79 p89
        """
        apply_proposition_type_kwargs = {}
        if "inject_proposition" in kwargs: # todo: tidy this up
            apply_proposition_type_kwargs["inject_proposition"] = kwargs.pop("inject_proposition", None)
        new_prop_type = self.apply_proposition_type(expressions, **apply_proposition_type_kwargs)
        return super().apply(*expressions, proposition_type=new_prop_type, **kwargs)

    def abstract(self, *expressions):
        """ [ST] p79 p89
        """
        from .proposition import implies, forall
        # check proof doesn't have expressions[0] free in self
        if self.proposition_type.contains_free(expressions[0]):
            if self.proposition_type.arity != forall.arity.lhs.args[1]:  # @UndefinedVariable
                warn("RHS doesn't match forall arity. forcing.")
                self.proposition_type.arity = forall.arity.lhs.args[1]  # @UndefinedVariable
            new_prop_type = forall(expressions[0], self.proposition_type)
        else:
            new_prop_type = implies(expressions[0].proposition_type, self.proposition_type)
        return super().abstract(*expressions, abstraction_kwargs={"proposition_type":new_prop_type})
  
class ProofSymbol(Symbol, 
                  metaclass=ProofExpressionMetaClass, 
                  expression_base_class=ProofExpression): pass
        
class ProofExpressionCombination(ExpressionCombination, 
                                 metaclass=ProofExpressionMetaClass, 
                                 expression_base_class=ProofExpression):
    """ [ST] p81 p91
    """
    def __init__(self, *args, **kwargs):
        from .proposition import and_, exists
        # todo: check only two proofs provided
        from .proposition import PropositionSubstitutionExpression
        #if args[1].proposition_type.contains_free(args[0]):
        if isinstance(args[1].proposition_type, PropositionSubstitutionExpression):
            self.proposition_type = exists(args[1].proposition_type.old, args[1].proposition_type)
        else:
            self.proposition_type = and_(args[0].proposition_type, args[1].proposition_type)
        super().__init__(*args, **kwargs)

    def compute(self, children=[]):
        return ProofExpressionCombination(*[c.compute() for c in self.children])

class ProofBaseWithChildrenExpression(BaseWithChildrenExpression, 
                                      metaclass=ProofExpressionMetaClass, 
                                      expression_base_class=ProofExpression): pass

class ProofApplicationExpression(ApplicationExpression, 
                                 metaclass=ProofExpressionMetaClass, 
                                 expression_base_class=ProofBaseWithChildrenExpression, 
                                 default_application_class=True):
    def compute(self, children=[]):
        computed_children = [c.compute([]) for c in self.children]
        return self.base.compute(computed_children)
        
class ProofAbstractionExpression(AbstractionExpression, 
                                 metaclass=ProofExpressionMetaClass, 
                                 expression_base_class=ProofBaseWithChildrenExpression, 
                                 default_abstraction_class=True):
    def apply_proposition_type(self, expressions, **kwargs):
        from .proposition import forall, implies
        if self.proposition_type.base == forall:
            # [ST] p90
            return self.proposition_type.children[1].substitute(self.proposition_type.children[0], expressions[0])
        elif self.proposition_type.base == implies:
            return self.proposition_type.children[1]
        else:
            raise PropositionException(f"Cannot apply if proposition is of type: {self.proposition_type.base}")
    
    def compute(self, children):
        """ [ST] p80 """
        if children:
            return self.base.replace(self.children[0], children[0])
        else:
            return self # nothing to compute

# definitions
# todo: check function inputs like .experimental.deduction_rules
#
class fstProofSymbol(ProofSymbol):
    """ [ST] p79
    """
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr, **kwargs):
        return expr[0].proposition_type.children[0]

    def compute(self, children):
        return children[0][0]
    
class sndProofSymbol(ProofSymbol):
    """ [ST] p79
    """    
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr, **kwargs):
        return expr[0].proposition_type.children[1]
    
    def compute(self, children):
        return children[0][1]    
    
class inlProofSymbol(ProofSymbol):
    """ [ST] p81
    """
    __default_arity__ = ArityArrow(A0, A0)
    def apply_proposition_type(self, expr, **kwargs):
        from .proposition import or_
        self._inject_proposition = kwargs["inject_proposition"] # todo: feels wrong?
        return or_(expr[0].proposition_type, kwargs["inject_proposition"])
    
    def compute(self, children):
        # todo: should we have a computation rule here?
        return self.apply(children[0], inject_proposition=self._inject_proposition)

class inrProofSymbol(ProofSymbol):
    """ [ST] p81
    """    
    __default_arity__ = ArityArrow(A0, A0)
    def apply_proposition_type(self, expr, **kwargs):
        from .proposition import or_
        self._inject_proposition = kwargs["inject_proposition"] # todo: feels wrong?
        return or_(kwargs["inject_proposition"], expr[0].proposition_type)
    
    def compute(self, children):
        # todo: should we have a computation rule here?
        return self.apply(children[0], inject_proposition=self._inject_proposition)
    
class CasesProofSymbol(ProofSymbol):
    """ [ST] p81
    """    
    __default_arity__ = ArityArrow(ArityCross(A0,ArityArrow(A0,A0),ArityArrow(A0,A0)), A0)
    def apply_proposition_type(self, expr, **kwargs):
        # todo: check inputs
        return expr[1].proposition_type.children[1]

    def compute(self, children):
        if children[0].base == inl:
            return children[1].apply(children[0].children[0])
        elif children[0].base == inr:
            return children[2].apply(children[0].children[0])
        else:
            return self
    
class FstProofSymbol(ProofSymbol):
    """ [ST] p91
    """
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr, **kwargs):
        #return expr[0].proposition_type.children[0].proposition_type
        return expr[0].proposition_type.children[0]
    
    def compute(self, children):
        return children[0][0]

class SndProofSymbol(ProofSymbol):
    """ [ST] p91
    """    
    __default_arity__ = ArityArrow(ArityCross(A0, A0), A0)
    def apply_proposition_type(self, expr, **kwargs):
        return expr[0].proposition_type.children[1] 
    
    def compute(self, children):
        return children[0][1]    
    
 
fst = fstProofSymbol('fst')
snd = sndProofSymbol('snd')
inl = inlProofSymbol('inl')
inr = inrProofSymbol('inr')
cases = CasesProofSymbol('cases') 
Fst = FstProofSymbol('Fst')
Snd = SndProofSymbol('Snd')

