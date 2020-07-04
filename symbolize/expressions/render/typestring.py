'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
from .base import Renderer

class TypeStringRendererMixin:
    def render_typestring(self, renderer):  # @UnusedVariable
        raise NotImplementedError()
    
class TypeStringRenderer(Renderer):
    def render(self, expression: "Expression") -> str:
        return expression.render_typestring(self)

        
