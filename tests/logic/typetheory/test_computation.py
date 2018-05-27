'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest

from symbolize.logic.typetheory.proposition import and_, implies, or_, forall, exists
from symbolize.logic.typetheory.proof import ProofExpressionCombination, ProofExpression, fst, snd, inl, inr, cases, Fst, Snd, ifthenelse
from symbolize.logic.typetheory.variables import A, B, C, bool_, True_, False_
#from symbolize.logic.typetheory.proposition import PropositionSymbol


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
        
        self.assertEqual(r.run(), e.substitute(x, a))
    
    @unittest.skip("Needs work")
    def test_cases_inl_inr(self):
        A_implies_C = implies(A, C)
        B_implies_C = implies(B, C)

        f = A_implies_C.get_proof('f')
        g = B_implies_C.get_proof('g')
        
        q = A.get_proof('q')
        r = B.get_proof('r')        

        r1 = cases(inl(q, B), f, g)
        self.assertEqual(r1.run(), f(q))

        r2 = cases(inr(r, A), f, g)
        self.assertEqual(r2.run(), g(r))
        
        
        