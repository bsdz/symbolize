"""natural: experimental natural number expression

symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from .expressions import Symbol, A0
from .expressions.extensions import InclusionExclusionExpression
from .definitions.operators import in_
from .definitions.sets import N


class NaturalNumber(InclusionExclusionExpression):
    def __init__(self, member_label):
        super().__init__(in_, [Symbol(member_label), N], A0)

    def render_latex_enable_wrap_parenthesis(self):
        return False
