'''
Created on 10 Jul 2017

@author: bsdz
'''
from .base import Renderer


class TypeStringRenderer(Renderer):
    def render(self) -> str:
        expression = self.expression
        rendered = ""
        if expression.baserepr is not None:
            rendered = expression.baserepr
        if expression.applications is not None:
            rendered += "(%s)" % (", ".join([TypeStringRenderer(e).render() for e in expression.applications]))
        if expression.abstractions is not None:
            rendered = "(%s)%s" % (", ".join([TypeStringRenderer(e).render() for e in expression.abstractions]), rendered)
        return rendered