
import unittest

from typetheory.expression import Expression, ExpressionException
from typetheory.definitions import plus

class ExpressionTest(unittest.TestCase):
    def test_expression_simple(self):
        self.assertEqual(repr(Expression('y')), 'y')
        self.assertEqual(repr(Expression('sin(y)')), 'sin(y)')
    
    def test_apply(self):
        y = Expression('y')
        sin_y = Expression('sin(y)')
        self.assertEqual(repr(plus.apply(y, sin_y)), '+(y, sin(y))')
        
    def test_apply_bad_arity(self):
        y = Expression('y')
        x = Expression('x')
        with self.assertRaises(ExpressionException) as cm:
            y.apply(x)
        self.assertIn("arity has no arrow", str(cm.exception))
        
    def test_abstract(self):
        y = Expression('y')
        sin_y = Expression('sin(y)')
        self.assertEqual(repr(plus.apply(y, sin_y).abstract(y)), '(y)+(y, sin(y))')
        
    def test_combination(self):
        x, y, z = [Expression(i) for i in ['x','y','z']]
        self.assertEqual(repr(Expression.combination(x,y,z)), 'x, y, z')
        
    def test_selection(self):
        x, y, z = [Expression(i) for i in ['x','y','z']]
        self.assertIs(Expression.combination(x,y,z).select(1), y)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()