'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest

from symbolize.expressions.arity import A0, ArityArrow
from symbolize.logic.typetheory.proposition import and_, implies, or_, forall, exists
from symbolize.logic.typetheory.proof import ProofExpressionCombination, ProofExpression, fst, snd, inl, inr, cases, Fst, Snd
from symbolize.logic.typetheory.boolean import bool_, True_, False_, ifthenelse
from symbolize.logic.typetheory.natural import N, succ, prim, zero
from symbolize.logic.typetheory.variables import A, B, C
from symbolize.logic.typetheory.proposition import PropositionSymbol


class TestComputationRules(unittest.TestCase):
    def test_fst_snd(self):
        p = A.get_proof('p')
        q = B.get_proof('q')
        
        r1 = fst(ProofExpressionCombination(p,q))
        self.assertEqual(r1.run(), p)
        
        r2 = snd(ProofExpressionCombination(p,q))
        self.assertEqual(r2.run(), q)
        
    def test_abstract(self):
        x = A.get_proof('x')
        e = B.get_proof('e')
        a = A.get_proof('a')
        
        r = e.abstract(x).apply(a)
        
        self.assertEqual(r.run(), e.replace(x, a))
    
    def test_cases_inl_inr(self):
        A_implies_C = implies(A, C)
        B_implies_C = implies(B, C)

        f = A_implies_C.get_proof('f')
        g = B_implies_C.get_proof('g')
        
        q = A.get_proof('q')
        r = B.get_proof('r')        

        r1 = cases(inl(q, inject_proposition=B), f, g)
        self.assertEqual(r1.run(), f(q))

        r2 = cases(inr(r, inject_proposition=A), f, g)
        self.assertEqual(r2.run(), g(r))
        
        
    def test_Fst_Snd(self):
        
        a = A.get_proof('a')
        x = A.get_proof('x')
        P = PropositionSymbol('P', assume_contains=[x]) #, arity=ArityArrow(A0,A0))
        p = P.get_proof('p')
        
        r1 = Fst(ProofExpressionCombination(a, p))
        self.assertEqual(r1.run(), a)
        
        r2 = Snd(ProofExpressionCombination(a, p))   
        self.assertEqual(r2.run(), p)
        
    def test_ifthenelse(self):
        
        C = PropositionSymbol('C')
        c = C.get_proof('c')
        d = C.get_proof('d')
        
        r1 = ifthenelse(True_, c, d)
        r2 = ifthenelse(False_, c, d)
        
        self.assertEqual(r1.run(), c)
        self.assertEqual(r2.run(), d)
        
    def test_prim_succ(self):
        
        n = N.get_proof('n')
        C = PropositionSymbol('C', assume_contains=[n], arity=ArityArrow(A0,A0))
        c = C.get_proof('c')
        
        
        Forall_n_C_implies_C = forall(n, implies(C, C))
        f = Forall_n_C_implies_C.get_proof('f')
        
        r1 = prim(zero, c, f)
        r2 = prim(succ(n), c, f)
        
        self.assertEqual(r1.run(), c)
        self.assertEqual(r2.run(), f(n).apply(prim(n, c, f)))
        