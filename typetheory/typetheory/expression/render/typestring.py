'''
Created on 10 Jul 2017

@author: bsdz
'''
from .base import Renderer


class TypeStringRenderer(Renderer):
    def render(self, expression: "Expression") -> str:
        rendered = ""
        if expression.baserepr is not None:
            rendered = expression.baserepr
        if expression.applications:
            rendered += "(%s)" % (", ".join([self.render(e) for e in expression.applications]))
        if expression.abstractions:
            rendered = "(%s)%s" % (", ".join([self.render(e) for e in expression.abstractions]), rendered)
        return rendered
