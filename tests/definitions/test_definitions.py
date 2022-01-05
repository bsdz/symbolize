'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest

from symbolize.definitions.misc import natrec, listrec
from symbolize.natural import NaturalNumber
from symbolize.definitions.functions import lambda_
from symbolize.definitions.variables import x, y


class DefinitionsTest(unittest.TestCase):
    def test_natrec(self):
        self.assertEqual(repr(natrec.arity), '(∅ ⨯ ∅ ⨯ ((∅ ⨯ ∅) ⟶ ∅)) ⟶ ∅')
    
    def test_listrec(self):
        self.assertEqual(repr(listrec.arity), '(∅ ⨯ ∅ ⨯ ((∅ ⨯ ∅ ⨯ ∅) ⟶ ∅)) ⟶ ∅')

    def test_natnum(self):
        n = NaturalNumber('n')
        tex = n.repr_latex()
        self.assertGreater(len(tex), 0)

    def test_lambda(self):
        inner = y.abstract(x)
        tex = lambda_(inner).repr_latex()
        self.assertGreater(len(tex), 0)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
