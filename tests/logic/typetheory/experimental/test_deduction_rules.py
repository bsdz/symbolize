'''
Created on 26 Aug 2017

@author: bsdz
'''
import unittest

from symbolize.expressions import A0, ArityArrow, ArityCross, ExpressionCombination

from symbolize.definitions.logic import and_, implies, or_
from symbolize.definitions.operators import pair
from symbolize.definitions.functions import fst, snd, inl, inr, cases

from symbolize.logic.typetheory.experimental.proposition import Proposition, get_proposition_class
from symbolize.logic.typetheory.experimental.deduction_rules import \
    conjunction_introduction, conjunction_elimination_1, conjunction_elimination_2, \
    implication_introduction, implication_elimation, \
    disjunction_introduction_1, disjunction_introduction_2, disjunction_elimination
from symbolize.logic.typetheory.experimental.variables import A, B, C


class TestDeductionRules(unittest.TestCase):

    def test_conjunction_introduction(self):
        p = A('p')
        q = B('q')
        
        r = conjunction_introduction(p,q)
        
        self.assertIsInstance(r, Proposition, "result is a proposition")
        self.assertEqual(r.proposition_expr, and_(A.proposition_expr, B.proposition_expr), "proof has correct expr")
        self.assertEqual(r.proof_expr, pair(p.proof_expr,q.proof_expr), "proof has correct expr")
        
    def test_conjunction_elimination(self):
        p = A('p')
        q = B('q')
        
        # test constructed conjunction
        r1 = conjunction_introduction(p,q)
        
        s11 = conjunction_elimination_1(r1)
        s12 = conjunction_elimination_2(r1)
        
        self.assertIsInstance(s11, Proposition, "result is a proposition")
        self.assertIsInstance(s12, Proposition, "result is a proposition")
        
        self.assertEqual(s11.proposition_expr, A.proposition_expr, "fst prop")
        self.assertEqual(s12.proposition_expr, B.proposition_expr, "snd prop")
        
        self.assertEqual(s11.proof_expr, fst(ExpressionCombination(p.proof_expr,q.proof_expr)), "proof has correct expr")
        self.assertEqual(s12.proof_expr, snd(ExpressionCombination(p.proof_expr,q.proof_expr)), "proof has correct expr")

        # test given conjunction
        A_and_B = get_proposition_class(and_(A.proposition_expr, B.proposition_expr))
        r2 = A_and_B('s2', arity=ArityCross(A0,A0))
        s21 = conjunction_elimination_1(r2)
        s22 = conjunction_elimination_2(r2)
        
        self.assertIsInstance(s21, Proposition, "result is a proposition")
        self.assertIsInstance(s22, Proposition, "result is a proposition")
        
        self.assertEqual(s21.proposition_expr, A.proposition_expr, "fst prop")
        self.assertEqual(s22.proposition_expr, B.proposition_expr, "snd prop")
        
        self.assertEqual(s21.proof_expr, fst(r2.proof_expr), "proof has correct expr")
        self.assertEqual(s22.proof_expr, snd(r2.proof_expr), "proof has correct expr")
        
    def test_implication_introduction(self):
        x = A('x')
        e = B('e')
        
        r = implication_introduction(x,e)
        
        self.assertIsInstance(r, Proposition, "result is a proposition")
        self.assertEqual(r.proposition_expr, implies(A.proposition_expr, B.proposition_expr), "proof has correct expr")
        self.assertEqual(r.proof_expr, e.proof_expr.abstract(x.proof_expr), "proof has correct expr")
        
    def test_implication_elimination(self):
        a = A('a')
        
        # test contructed implication
        x = A('x')
        e = B('e')
        r1 = implication_introduction(x,e)
        
        s1 = implication_elimation(r1, a)
        self.assertIsInstance(s1, Proposition, "result is a proposition")
        self.assertEqual(s1.proposition_expr, B.proposition_expr, "correct prop")
        # todo: is this correct? r1 is already abstracted
        self.assertEqual(s1.proof_expr, r1.proof_expr.apply(a.proof_expr), "proof has correct expr")
        
        # test give implication
        A_implies_B = get_proposition_class(implies(A.proposition_expr, B.proposition_expr))
        r2 = A_implies_B('r2', arity=ArityArrow(A0,A0))
        
        s2 = implication_elimation(r2, a)
        self.assertIsInstance(s2, Proposition, "result is a proposition")
        self.assertEqual(s2.proposition_expr, B.proposition_expr, "correct prop")
        self.assertEqual(s2.proof_expr, r2.proof_expr.apply(a.proof_expr), "proof has correct expr")

    def test_disjunction_introduction(self):
        q = A('q')
        r = B('r')

        s1 = disjunction_introduction_1(q, B)

        self.assertIsInstance(s1, Proposition, "result is a proposition")
        self.assertEqual(s1.proposition_expr, or_(A.proposition_expr, B.proposition_expr), "proof has correct expr")
        self.assertEqual(s1.proof_expr, inl(q.proof_expr), "proof has correct expr")

        s2 = disjunction_introduction_2(r, A)

        self.assertIsInstance(s2, Proposition, "result is a proposition")
        self.assertEqual(s2.proposition_expr, or_(A.proposition_expr, B.proposition_expr), "proof has correct expr")
        self.assertEqual(s2.proof_expr, inr(r.proof_expr), "proof has correct expr")

    def test_disjunction_elimination(self):
        
        A_implies_C = get_proposition_class(implies(A.proposition_expr, C.proposition_expr))
        B_implies_C = get_proposition_class(implies(B.proposition_expr, C.proposition_expr))

        f = A_implies_C('f')
        g = B_implies_C('g')

        # test constructed disjunction
        q = A('q')
        r = B('r')

        p1 = disjunction_introduction_1(q, B)
        p2 = disjunction_introduction_2(r, A)

        s1 = disjunction_elimination(p1, f, g)
        self.assertIsInstance(s1, Proposition, "result is a proposition")
        self.assertEqual(s1.proposition_expr, C.proposition_expr, "proof has correct expr")
        self.assertEqual(s1.proof_expr, cases(p1.proof_expr, f.proof_expr, g.proof_expr), "proof has correct expr")

        s2 = disjunction_elimination(p2, f, g)
        self.assertIsInstance(s2, Proposition, "result is a proposition")
        self.assertEqual(s2.proposition_expr, C.proposition_expr, "proof has correct expr")
        self.assertEqual(s2.proof_expr, cases(p2.proof_expr, f.proof_expr, g.proof_expr), "proof has correct expr")

        # test given disjunction
        A_or_B = get_proposition_class(or_(A.proposition_expr, B.proposition_expr))
        p3 = A_or_B('p3')
        
        s3 = disjunction_elimination(p3, f, g)
        self.assertIsInstance(s3, Proposition, "result is a proposition")
        self.assertEqual(s3.proposition_expr, C.proposition_expr, "proof has correct expr")
        self.assertEqual(s3.proof_expr, cases(p3.proof_expr, f.proof_expr, g.proof_expr), "proof has correct expr")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()