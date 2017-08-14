"""
Created on 8 Jul 2017

@author: bsdz
"""
import unittest
from typetheory.expressions import Expression
from typetheory.definitions.operators import plus
from typetheory.definitions.integrals import integral
from typetheory.expressions.render.graph import GraphRenderer


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
        
    def test_render_latex_binary_infix(self):
        a = Expression('a')
        b = Expression('b')
        rendered = plus.apply(a, b).render_latex()
        self.assertGreater(len(rendered), 0)

    def test_render_graph(self):
        a = Expression('a')
        b = Expression('b')
        x = Expression('x')
        y = Expression('y')
        sin_y = Expression('sin(y)')
        #expr = integral.apply(plus.apply(y, sin_y).abstract(y), a, b)
        #expr = plus.apply(y, sin_y)
        expr = plus.apply(x,plus.apply(x, y))
        graph = GraphRenderer().render(expr)
        self.assertIsNotNone(graph)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
