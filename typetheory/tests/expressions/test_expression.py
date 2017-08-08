
import unittest

from typetheory.expressions import Expression, ExpressionException, ExpressionCombination
from typetheory.expressions.arity import ArityArrow, ArityCross, A0

plus = Expression('+', arity=ArityArrow(ArityCross(A0,A0),A0))

class ExpressionTest(unittest.TestCase):
    def test_expression_simple(self):
        self.assertEqual(repr(Expression('y')), 'y')
        self.assertEqual(repr(Expression('sin(y)')), 'sin(y)')
    
    def test_apply(self):
        y = Expression('y')
        sin_y = Expression('sin(y)')
        self.assertEqual(repr(plus.apply(y, sin_y)), '+(y, sin(y))')
        
        x = Expression('x')
        z = Expression('z', ArityArrow(ArityCross(A0,A0),A0))
        self.assertEqual(repr(z.apply(x,y)), 'z(x, y)')
        self.assertEqual(z.apply(x,y).arity, A0, "correct arity after apply")
        
        sin = Expression('sin', arity=ArityArrow(A0,A0))
        self.assertEqual(sin.apply(x).arity, A0, "correct arity after apply")
        
    def test_apply_bad_arity(self):
        y = Expression('y')
        x = Expression('x')
        with self.assertRaises(ExpressionException) as cm:
            y.apply(x)
        self.assertIn("arity has no arrow", str(cm.exception))
        
        z = Expression('z', ArityArrow(ArityCross(A0,A0),A0))
        sin = Expression('sin', ArityArrow(A0,A0))
        with self.assertRaises(ExpressionException) as cm:
            z.apply(x,sin)
        self.assertIn("does not match child arity", str(cm.exception))
        
    def test_abstract(self):
        y = Expression('y')
        sin_y = Expression('sin(y)')
        self.assertEqual(repr(plus.apply(y, sin_y).abstract(y)), '(y)+(y, sin(y))')
        
        self.assertEqual(plus.apply(y, sin_y).abstract(y).arity, ArityArrow(A0,A0), "arity from abstration")
        
    def test_combination(self):
        x, y, z = [Expression(i) for i in ['x','y','z']]
        self.assertEqual(repr(ExpressionCombination(x,y,z)), 'x, y, z')
        self.assertEqual(ExpressionCombination(x,y,z).arity, ArityCross(A0,A0,A0), "arity from combination")
        
    def test_selection(self):
        x, y, z = [Expression(i) for i in ['x','y','z']]
        self.assertEqual(ExpressionCombination(x,y,z).select(1), y)
        self.assertEqual(ExpressionCombination(x,y,z).select(1).arity, A0, "arity from selection")
    
    def test_walk(self):
        u,v,w,x,y,z = [Expression(i) for i in 'uvwxyz']
        self.assertIn(x,x, "same expr")
        
        u.arity = ArityArrow(ArityCross(A0,A0),A0)
        w.arity = ArityArrow(ArityCross(A0,A0,A0),A0)
        
        collected = []
        func1 = lambda *args: collected.append(args)
        u(v, w(x,y,z)).walk(func1)
        self.assertGreater(len(collected), 0, "collect data")
        
        collected2 = []
        def func2(*args): 
            collected2.append(args)
            if type(args[0]) is Expression and args[0] == x:
                raise Exception("Found")
        
        try:    
            u(v, w(x,y,z)).walk(func2)
        except:
            pass
        self.assertGreater(len(collected2), 0, "collect data")
        
        self.assertGreater(len(collected), len(collected2), "collect data")
        
        
    def test_contains(self):
        u,v,w,x,y,z = [Expression(i) for i in 'uvwxyz']
        self.assertIn(x,x, "same expr")
        
        u.arity = ArityArrow(ArityCross(A0,A0),A0)
        w.arity = ArityArrow(ArityCross(A0,A0,A0),A0)
        self.assertIn(x, u(v, w(x,y,z)), "in nested expr")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()