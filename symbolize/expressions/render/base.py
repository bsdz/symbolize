"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..expression import Expression


class Renderer:
    def render(self, expression: "Expression"):
        raise NotImplementedError()
