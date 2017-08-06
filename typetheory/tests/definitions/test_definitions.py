
import unittest

from typetheory.definitions.misc import natrec, listrec
from typetheory.natural import NaturalNumber


class DefinitionsTest(unittest.TestCase):
    def test_natrec(self):
        self.assertEqual(repr(natrec.arity), '(0 x 0 x ((0 x 0) -> 0)) -> 0')
    
    def test_listrec(self):
        self.assertEqual(repr(listrec.arity), '(0 x 0 x ((0 x 0 x 0) -> 0)) -> 0')
        
    def test_natnum(self):
        n = NaturalNumber('n')
        lt = n.render_latex()
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()