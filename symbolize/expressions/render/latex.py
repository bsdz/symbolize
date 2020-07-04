'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

from .base import Renderer

class LatexRendererMixin:
    def render_latex(self, renderer):  # @UnusedVariable
        raise NotImplementedError()
    
    def render_latex_enable_wrap_parenthesis(self):
        return True
    
    def render_latex_wrap_parenthesis(self, renderer):
        """wraps expression in parenthesis if application"""
        from ..expression import ApplicationExpression
        if isinstance(self, ApplicationExpression) and self.render_latex_enable_wrap_parenthesis():
            return "(%s)" % self.render_latex(renderer)
        else:
            return "%s" % self.render_latex(renderer)

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
        
        