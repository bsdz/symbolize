'''
Created on 7 Sep 2017

@author: bsdz
'''
import unittest

from symbolize.logic.typetheory.proposition import and_, implies, or_
from symbolize.logic.typetheory.proof import ProofExpressionCombination, ProofExpression, fst, snd, inl, inr, cases
from symbolize.logic.typetheory.variables import A, B, C


class TestDeductionRules(unittest.TestCase):

    def test_conjunction_introduction(self):
        p = A.get_proof('p')
        q = B.get_proof('q')
        
        r = ProofExpressionCombination(p,q)
        
        self.assertIsInstance(r, ProofExpression, "result is a proof")
        self.assertEqual(r.proposition_type, and_(A, B), "proof has correct type")
    
    def test_conjunction_elimination(self):
        p = A.get_proof('p')
        q = B.get_proof('q')
        
        # test constructed conjunction
        r1 = ProofExpressionCombination(p,q)
        
        s11 = fst(r1)
        s12 = snd(r1)
        
        self.assertIsInstance(s11, ProofExpression, "result is a proof")
        self.assertIsInstance(s12, ProofExpression, "result is a proof")
        
        self.assertEqual(s11.proposition_type, A, "fst prop")
        self.assertEqual(s12.proposition_type, B, "snd prop")
        
        ## test given conjunction
        A_and_B = and_(A, B)
        r2 = A_and_B.get_proof('s2') #, arity=ArityCross(A0,A0))
        s21 = fst(r2)
        s22 = snd(r2)
        
        self.assertIsInstance(s21, ProofExpression, "result is a proof")
        self.assertIsInstance(s22, ProofExpression, "result is a proof")
        
        self.assertEqual(s21.proposition_type, A, "fst prop")
        self.assertEqual(s22.proposition_type, B, "snd prop")
        
    def test_implication_introduction(self):
        x = A.get_proof('x')
        e = B.get_proof('e')
        
        r = e.abstract(x)
        
        self.assertIsInstance(r, ProofExpression, "result is a proof")
        self.assertEqual(r.proposition_type, implies(A, B), "proof has correct expr")
        
    def test_implication_elimination(self):
        a = A.get_proof('a')
        
        # test contructed implication
        x = A.get_proof('x')
        e = B.get_proof('e')
        r1 = e.abstract(x)
        
        s1 = r1.apply(a)
        self.assertIsInstance(s1, ProofExpression, "result is a proof")
        self.assertEqual(s1.proposition_type, B, "correct prop")
        
        # test give implication
        A_implies_B = implies(A, B)
        r2 = A_implies_B.get_proof('r2') #, arity=ArityArrow(A0,A0))
        
        s2 = r2.apply(a)
        self.assertIsInstance(s2, ProofExpression, "result is a proof")
        self.assertEqual(s2.proposition_type, B, "correct prop")

    def test_disjunction_introduction(self):
        q = A.get_proof('q')
        r = B.get_proof('r')

        s1 = inl(q, B)

        self.assertIsInstance(s1, ProofExpression, "result is a proof")
        self.assertEqual(s1.proposition_type, or_(A, B), "proof has correct expr")

        s2 = inr(r, A)

        self.assertIsInstance(s2, ProofExpression, "result is a proof")
        self.assertEqual(s2.proposition_type, or_(A, B), "proof has correct expr")

    def test_disjunction_elimination(self):
        
        A_implies_C = implies(A, C)
        B_implies_C = implies(B, C)

        f = A_implies_C.get_proof('f')
        g = B_implies_C.get_proof('g')

        # test constructed disjunction
        q = A.get_proof('q')
        r = B.get_proof('r')

        p1 = inl(q, B)
        p2 = inr(r, A)

        s1 = cases(p1, f, g)
    #    self.assertIsInstance(s1, Proposition, "result is a proposition")
    #    self.assertEqual(s1.proposition_expr, C.proposition_expr, "proof has correct expr")
    #    self.assertEqual(s1.proof_expr, cases(p1.proof_expr, f.proof_expr, g.proof_expr), "proof has correct expr")

    #    s2 = disjunction_elimination(p2, f, g)
    #    self.assertIsInstance(s2, Proposition, "result is a proposition")
    #    self.assertEqual(s2.proposition_expr, C.proposition_expr, "proof has correct expr")
    #    self.assertEqual(s2.proof_expr, cases(p2.proof_expr, f.proof_expr, g.proof_expr), "proof has correct expr")

    #    # test given disjunction
    #    A_or_B = get_proposition_class(or_(A.proposition_expr, B.proposition_expr))
    #    p3 = A_or_B('p3')
        
    #    s3 = disjunction_elimination(p3, f, g)
    #    self.assertIsInstance(s3, Proposition, "result is a proposition")
    #    self.assertEqual(s3.proposition_expr, C.proposition_expr, "proof has correct expr")
    #    self.assertEqual(s3.proof_expr, cases(p3.proof_expr, f.proof_expr, g.proof_expr), "proof has correct expr")

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
