'''
Created on 10 Jul 2017

@author: bsdz
'''
from textwrap import dedent
import jinja2

from .base import Renderer
from ...utility import extend_instance

class LatexRendererExpressionMixin(object):
    def render_latex_baserepr(self, renderer):  # @UnusedVariable
        return self.latexrepr
    
    def render_latex_applications(self, renderer):
        return ", ".join([renderer.render(e) for e in self.applications]) if hasattr(self,"applications") and self.applications else None
    
    def render_latex_abstractions(self, renderer):
        return ", ".join([renderer.render(e) for e in self.abstractions]) if hasattr(self,"abstractions") and self.abstractions else None
    
    def render_latex_parenthesize_applications(self, renderer):  # @UnusedVariable
        return self.parent is not None or self.render_latex_baserepr(renderer) is not None

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
        
        baserepr_rendered = expression.render_latex_baserepr(self)
        applications_rendered = expression.render_latex_applications(self)
        abstractions_rendered = expression.render_latex_abstractions(self)
        parenthesize_applications = expression.render_latex_parenthesize_applications(self)
        
        # we genrate postfix only if we are top level expression, i.e no parent
        postfix = "".join([h(self) for h in self.postfix_hooks]) if expression.parent is None and self.postfix_hooks else None
                
        template = dedent("""\
            {% if abstractions != None %}\\lambda({{abstractions}}).({% endif %}
            {{ baserepr if baserepr != None else '' }}
            {% if applications != None %}
            {% if parenthesize_applications %}({% endif %}
            {{applications}}
            {% if parenthesize_applications %}){% endif %}
            {% endif %}
            {% if abstractions != None %}){% endif %}
            {% if postfix != None %}\quad{{postfix}}{% endif %}
            """).replace("\n", "").replace("\r", "")
        
        return self.jinja2_env.from_string(template).render(
            expression=expression, 
            baserepr=baserepr_rendered,
            applications=applications_rendered,
            abstractions=abstractions_rendered,
            parenthesize_applications=parenthesize_applications,
            postfix=postfix)
        