'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest
from symbolize.expressions import Symbol
from symbolize.definitions.operators import plus, mult
from symbolize.definitions.integrals import integral
from symbolize.expressions.extensions import InclusionExclusionSymbol


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
        expr = InclusionExclusionSymbol('in', latex_repr=r'\in').apply(x,y)
        rendered = expr.repr_latex()
        self.assertEqual(r'x\quad[x \in y]', rendered)
        
    def test_parenthesis(self):
        x,y,z = [Symbol(i) for i in 'xyz']
        expr = mult(z,plus(x, y))
        rendered = expr.repr_latex()
        self.assertEqual(r"z \cdot (x + y)", rendered)

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
