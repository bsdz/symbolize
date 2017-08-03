'''
Created on 16 Jul 2017

@author: bsdz
'''

from .utility import generate_random_string

class Argument(object):
    """support a list of true or false statements (premises) that 
    have a conclusion."""
    def __init__(self, name="", premises = [], conclusion = None):
        self._name = name or "argument_" + generate_random_string(6)
        self._premises = premises 
        self._conclusion = conclusion

    @property
    def name(self):
        """str: argument name."""
        return self._name
  
    @property
    def premises(self):
        """List[Expression]: list of premise statements."""
        return self._premises
    
    @property
    def conclusion(self):
        """Expression: conclusion statement."""
        return self._conclusion