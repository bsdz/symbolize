"""
Created on 8 Jul 2017

@author: bsdz
"""
import unittest
from typetheory.expressions import Symbol
from typetheory.definitions.operators import plus
from typetheory.definitions.integrals import integral
from typetheory.expressions.extensions import InclusionExclusionSymbol


class RendererTest(unittest.TestCase):

    def test_render_latex(self):
        y = Symbol('y')
        sin_y = Symbol('sin(y)')
        rendered = plus(y, sin_y).abstract(y).repr_latex()
        self.assertGreater(len(rendered), 0)
        
    def test_render_latex_integral(self):
        a = Symbol('a')
        b = Symbol('b')
        y = Symbol('y')
        sin_y = Symbol('sin(y)')
        rendered = integral(plus(y, sin_y).abstract(y), a, b).repr_latex()
        self.assertGreater(len(rendered), 0)
        
    def test_render_latex_binary_infix(self):
        a = Symbol('a')
        b = Symbol('b')
        rendered = plus(a, b).repr_latex()
        self.assertGreater(len(rendered), 0)
        
    def test_render_latex_inclusionexclusion(self):
        x = Symbol('x')
        y = Symbol('y')
        expr = InclusionExclusionSymbol('e').apply(x,y)
        rendered = expr.repr_latex()
        self.assertEqual("foo", rendered)

    def test_render_graph(self):
        x = Symbol('x')
        y = Symbol('y')
        expr = plus(x,plus(x, y)).abstract(y)
        graph = expr.repr_graphtool()
        self.assertIsNotNone(graph)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
