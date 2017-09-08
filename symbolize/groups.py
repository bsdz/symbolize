'''
Created on 16 Jul 2017

@author: bsdz
'''

from .expressions import Symbol, InclusionExclusionExpression, BinaryInfixSymbol, ArityArrow, ArityCross, A0
from .definitions.operators import in_
from .logic.proof import Argument

make_group = Symbol('Group', arity=ArityArrow(ArityCross(A0,ArityArrow(ArityCross(A0,A0),A0)),A0))
G_set = Symbol('G') # generic group set
op = BinaryInfixSymbol('.', latex_repr=r'\cdot') # generic group operation
G = make_group(G_set, op)

class GroupMember(InclusionExclusionExpression):
    def __init__(self, member_label):
        super().__init__(in_, [Symbol(member_label), G], A0)
        
    def render_latex_enable_wrap_parenthesis(self):
        return False

# generic members
a = GroupMember('a')
b = GroupMember('b')

axiom_closure = Argument(
    name = "group_closure", 
    premises = [a, b],
    conclusion = [in_(op.apply(a,b),G)]
)


