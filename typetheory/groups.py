'''
Created on 16 Jul 2017

@author: bsdz
'''

from .expression import Expression, InclusionExclusionExpression, BinaryInfixExpression, ArityArrow, ArityCross, A0
from .definitions.operators import in_
from .proof import Argument

make_group = Expression('Group', arity=ArityArrow(ArityCross(A0,ArityArrow(ArityCross(A0,A0),A0)),A0))
G_set = Expression('G') # genric group set
op = BinaryInfixExpression('.', latexrepr=r'\cdot') # generic group operation
G = make_group.apply(G_set, op)

class GroupMember(InclusionExclusionExpression):
    def __init__(self, member_label):
        super(GroupMember, self).__init__('in', latexrepr=r'\in')
        new_obj = self.apply(Expression(member_label), G)
        self.__dict__.update(new_obj.__dict__)

# generic members
a = GroupMember('a')
b = GroupMember('b')

axiom_closure = Argument(
    name = "group_closure", 
    premises = [a, b],
    conclusion = [in_.apply(op.apply(a,b),G)]
)


