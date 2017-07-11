"""
Created on 8 Jul 2017

@author: bsdz
"""
import unittest
from typetheory.expression import Expression
from typetheory.definitions import plus, integral
from typetheory.render.graph import GraphRenderer


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

    def test_render_graph(self):
        a = Expression('a')
        b = Expression('b')
        y = Expression('y')
        sin_y = Expression('sin(y)')
        expr = integral.apply(plus.apply(y, sin_y).abstract(y), a, b)
        graph = GraphRenderer(expr).render()
        self.assertIsNotNone(graph)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
