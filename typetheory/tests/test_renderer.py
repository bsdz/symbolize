'''
Created on 8 Jul 2017

@author: bsdz
'''
import unittest
from typetheory.expression import Expression, ExpressionException, ExpressionCombination
from typetheory.arity import ArityArrow, ArityCross, A0
from typetheory.definitions import plus, integral

class RendererTest(unittest.TestCase):


    def test_render_latex(self):
        y = Expression('y')
        sin_y = Expression('sin(y)')
        rendered = plus.apply(y, sin_y).abstract(y).render_latex()
        self.assertGreater(len(rendered), 0)
        
    def test_render_latex_integral(self):
        a = Expression('a')
        b = Expression('b')
        y = Expression('y')
        sin_y = Expression('sin(y)')
        rendered = integral.apply(plus.apply(y, sin_y).abstract(y), a, b).render_latex()
        self.assertGreater(len(rendered), 0)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()