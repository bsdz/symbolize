'''
Created on 16 Jul 2017

@author: bsdz
'''

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
    
    def render_latex(self):
        top_tex = r" \quad ".join([p.render_latex() for p in self._premises])
        if self._discharges:
            top_tex = r"""\begin{matrix}
            [%s]\\
            \vdots\\
            %s\\
            \end{matrix}""" % (r" \quad ".join([p.render_latex() for p in self._discharges]), top_tex)
        
        return r"\frac{%s}{%s}%s" % (top_tex, self._conclusion.render_latex(),
                                     "(%s)" % self._label if self._label else "")
    
    def _repr_latex_(self):
        """For Jupyter/IPython"""
        return "$$%s$$" % self.render_latex()
    