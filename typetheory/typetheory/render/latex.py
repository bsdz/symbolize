'''
Created on 10 Jul 2017

@author: bsdz
'''
from textwrap import dedent
import jinja2

from .base import Renderer

#class LatexRenderMixin(object):
#    def render_latex_baserepr(self, ):

class LatexRenderer(Renderer):
    """
    will except overrides for
    expression.render_latex_baserepr,
    expression.render_latex_applications and 
    expression.render_latex_abstractions
    """
    def __init__(self):
        super(LatexRenderer, self).__init__()
        self.jinja2_env = jinja2.Environment(trim_blocks=True,autoescape=False)
        self.jinja2_env.globals["LatexRenderer"] = LatexRenderer
        self.postfix_hooks = [] # function that generate latex for postfix 

    def render(self, expression: "Expression") -> str:
        baserepr_rendered = expression.latexrepr
        if hasattr(expression, "render_latex_baserepr"):
            baserepr_rendered = expression.render_latex_baserepr(self)

        applications_rendered = None
        if expression.applications:
            if hasattr(expression, "render_latex_applications"):
                applications_rendered = expression.render_latex_applications(self)
            else:
                applications_rendered = ", ".join([self.render(e) for e in expression.applications])
        
        abstractions_rendered = None
        if expression.abstractions:
            if hasattr(expression, "render_latex_abstractions"):
                abstractions_rendered = expression.render_latex_abstractions(self)
            else:
                abstractions_rendered = ", ".join([self.render(e) for e in expression.abstractions])
        
        # we genrate postfix only if we are top level expression, i.e no parent
        postfix = "".join([h(self) for h in self.postfix_hooks]) if expression.parent is None and self.postfix_hooks else None
                
        template = dedent("""\
            {% if abstractions != None %}\\lambda({{abstractions}}).({% endif %}
            {{ baserepr if baserepr != None else '' }}
            {% if applications != None %}
            {% if expression.parent is not none %}({% endif %}
            {{applications}}
            {% if expression.parent is not none %}){% endif %}
            {% endif %}
            {% if abstractions != None %}){% endif %}
            {% if postfix != None %}\quad{{postfix}}{% endif %}
            """).replace("\n", "").replace("\r", "")
        
        return self.jinja2_env.from_string(template).render(
            expression=expression, 
            baserepr=baserepr_rendered,
            applications=applications_rendered,
            abstractions=abstractions_rendered,
            postfix=postfix)
        