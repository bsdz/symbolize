"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""
from typing import TYPE_CHECKING
from .base import Renderer

if TYPE_CHECKING:
    from ..expression import Expression


class TypeStringRendererMixin:
    def render_typestring(self, renderer):
        raise NotImplementedError()


class TypeStringRenderer(Renderer):
    def render(self, expression: "Expression") -> str:
        return expression.render_typestring(self)
