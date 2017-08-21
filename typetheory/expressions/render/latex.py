'''
Created on 10 Jul 2017

@author: bsdz
'''

from .base import Renderer

class LatexRendererMixin(object):
    def render_latex(self, renderer):  # @UnusedVariable
        raise NotImplementedError()

class LatexRenderer(Renderer):
    def __init__(self):
        super().__init__()
        self.postfix_hooks = [] # function that generate latex for postfix 

    def render(self, expression: "Expression") -> str:
        
        rendered = expression.render_latex(self)
        
        # we genrate postfix only if we are top level expression, i.e no parent
        if self.postfix_hooks:
            postfix = "".join([h(self) for h in self.postfix_hooks])
            rendered += r"\quad" + postfix
             
        return rendered
        
        