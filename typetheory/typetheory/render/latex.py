'''
Created on 10 Jul 2017

@author: bsdz
'''
from textwrap import dedent
import jinja2

from .base import Renderer


class LatexRenderer(Renderer):
    """
    will except overrides for
    expression.render_latex_baserepr,
    expression.render_latex_applications and 
    expression.render_latex_abstractions
    """
    def __init__(self, expression: "Expression"):
        super(LatexRenderer, self).__init__(expression)
        self.jinja2_env = jinja2.Environment(trim_blocks=True,autoescape=False)
        self.jinja2_env.globals["LatexRenderer"] = LatexRenderer

    def render(self) -> str:
        baserepr_rendered = self.expression.latexrepr
        if hasattr(self.expression, "render_latex_baserepr"):
            baserepr_rendered = self.expression.render_latex_baserepr()

        applications_rendered = None
        if self.expression.applications is not None:
            if hasattr(self.expression, "render_latex_applications"):
                applications_rendered = self.expression.render_latex_applications()
            else:
                applications_rendered = ", ".join([LatexRenderer(e).render() for e in self.expression.applications])
        
        abstractions_rendered = None
        if self.expression.abstractions is not None:
            if hasattr(self.expression, "render_latex_abstractions"):
                abstractions_rendered = self.expression.render_latex_abstractions()
            else:
                abstractions_rendered = ", ".join([LatexRenderer(e).render() for e in self.expression.abstractions])
                
        template = dedent("""\
            {% if abstractions != None %}\\lambda({{abstractions}}).({% endif %}
            {{ baserepr if baserepr != None else '' }}
            {% if applications != None %}{{applications}}{% endif %}
            {% if abstractions != None %}){% endif %}""").replace("\n", "").replace("\r", "")
        
        return self.jinja2_env.from_string(template).render(
            expression=self.expression, 
            baserepr=baserepr_rendered,
            applications=applications_rendered,
            abstractions=abstractions_rendered)
        