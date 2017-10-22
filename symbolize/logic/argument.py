'''argument: logical argument representation

symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
from textwrap import dedent

from ..expressions import Expression, Symbol
from ..utility import generate_random_string

class Argument(object):
    
    """support a list of true or false statements (premises) that 
    have a conclusion."""
    def __init__(self, premises = [], conclusion = None, name="", discharges=[], label=""):
        self._name = name or "argument_" + generate_random_string(6)
        self._premises = premises 
        self._conclusion = conclusion
        self._discharges = discharges
        self._label = label

    @property
    def name(self):
        """str: argument name."""
        return self._name
  
    @property
    def premises(self):
        """List[Proposition]: list of premise statements."""
        return self._premises
    
    @property
    def conclusion(self):
        """Proposition: conclusion statement."""
        return self._conclusion
    
    @property
    def discharges(self):
        """List[Proposition]: list of discharge statements."""
        return self.discharges
    
    def repr_latex(self):
        top_tex = r" \quad ".join([p.repr_latex() for p in self._premises])
        if self._discharges:
            top_tex = r"""\begin{matrix}
            [%s]\\
            \vdots\\
            %s\\
            \end{matrix}""" % (r" \quad ".join([p.repr_latex() for p in self._discharges]), top_tex)
        
        return r"\frac{%s}{%s}%s" % (top_tex, self._conclusion.repr_latex(),
                                     "(%s)" % self._label if self._label else "")
        
    def repr_html(self):
        top_tex = """<table>
        <tr><td style="valign='bottom';">%s</td></tr>
        </table>""" % """</td><td style="vertical-align:bottom">""".join([p.repr_html() if hasattr(p, "repr_html") else p.repr_unicode() for p in self._premises])
        if self._discharges:
            top_tex = """<table>
            <tr><td>[%s]</td></tr>
            <tr><td>:</td></tr>
            <tr><td>%s</td></tr>
            </table>""" % (r"   ".join([p.repr_html() if hasattr(p, "repr_html") else p.repr_unicode() for p in self._discharges]), top_tex)
        
        without_label = """<table>
        <tr><td style="border-bottom: 1px solid black !important;">%s</td></tr>
        <tr><td style='text-align:center;background-color:white'>%s</td></tr>
        </table>""" % (top_tex, self._conclusion.repr_unicode())
        
        if self._label:
            return """<table>
            <tr><td>%s</td><td>(%s)</td></tr>
            <table>""" % (without_label, self._label)
        else:
            return without_label
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return Expression.jupyter_repr_latex_function(self)
    
    def _repr_html_(self):
        """For Jupyter/IPython"""
        if Expression.jupyter_repr_html_function(Symbol('_dummy_')) is None:
            return None
        return self.repr_html()
            
            
    