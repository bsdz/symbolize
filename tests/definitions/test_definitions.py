
import unittest

from symbolize.definitions.misc import natrec, listrec
from symbolize.natural import NaturalNumber
from symbolize.definitions.functions import lambda_
from symbolize.definitions.variables import *


class DefinitionsTest(unittest.TestCase):
    def test_natrec(self):
        self.assertEqual(repr(natrec.arity), '(∅ ⨯ ∅ ⨯ ((∅ ⨯ ∅) ⟶ ∅)) ⟶ ∅')
    
    def test_listrec(self):
        self.assertEqual(repr(listrec.arity), '(∅ ⨯ ∅ ⨯ ((∅ ⨯ ∅ ⨯ ∅) ⟶ ∅)) ⟶ ∅')

    def test_natnum(self):
        n = NaturalNumber('n')
        tex = n.repr_latex()
        self.assertGreater(len(tex), 0, "returns some tex")

    def test_lambda(self):
        inner = y.abstract(x)
        tex = lambda_(inner).repr_latex()
        self.assertGreater(len(tex), 0, "returns some tex")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()