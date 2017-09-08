'''
Created on 10 Jul 2017

@author: bsdz
'''
from .base import Renderer

class TypeStringRendererMixin(object):
    def render_typestring(self, renderer):  # @UnusedVariable
        raise NotImplementedError()
    
class TypeStringRenderer(Renderer):
    def render(self, expression: "Expression") -> str:
        return expression.render_typestring(self)

        
