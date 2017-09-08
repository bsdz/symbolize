'''
Created on 30 Mar 2017

@author: blair
'''
import unittest

from symbolize.expressions.arity import A0, ArityPlaceHolder, ArityCross, ArityArrow


class ArityTest(unittest.TestCase):
    def test_arity_simple(self):
        self.assertEqual(repr(ArityPlaceHolder()), '∅')
        self.assertEqual(repr(A0), '∅')

    def test_arity_cross(self):
        self.assertEqual(repr(ArityCross(A0, A0)), '∅ ⨯ ∅')

    def test_arity_arrow_cross(self):
        self.assertEqual(repr(ArityArrow(A0,ArityCross(A0,A0))), '∅ ⟶ (∅ ⨯ ∅)')

    def test_arity_arrow(self):
        self.assertEqual(repr(ArityArrow(A0,A0)), '∅ ⟶ ∅')

    def test_arity_equivalence(self):
        self.assertEqual(A0, A0)
        self.assertEqual(ArityArrow(A0,ArityCross(A0,A0)), ArityArrow(A0,ArityCross(A0,A0)))


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()