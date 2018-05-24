'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest

from symbolize.expressions import Symbol
from symbolize.logic.typetheory.proposition import and_, implies, or_, forall, exists
from symbolize.logic.typetheory.proof import ProofExpressionCombination, ProofExpression, fst, snd, inl, inr, cases, Fst, Snd
from symbolize.logic.typetheory.variables import A, B, C
from symbolize.logic.typetheory.proposition import PropositionSymbol

class TestDeductionRules(unittest.TestCase):
    
    def test_A_or_B_deduce_B_or_A(self):
        """ [ST] p72 """
        
        p = A.get_proof('p')
        q = B.get_proof('q')
        r1 = ProofExpressionCombination(p,q)
        
        r2 = ProofExpressionCombination(
            snd(r1),
            fst(r1)
        )
        
        outputs = {
            r1: and_(A, B),
            r2: and_(B, A),
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")        
        
        
    def test_identity(self):
        """ [ST] p83 """
        
        x = A.get_proof('x')
        
        r = x.abstract(x)
        
        self.assertIsInstance(r, ProofExpression, "result is a proof")
        self.assertEqual(r.proposition_type, implies(A, A), "proof has correct expr")
        
    def test_A_implies_B_implies_C_both_imply_A_implies_C(self):
        """ [ST] p83-84 """
        
        A_implies_B = implies(A, B)
        B_implies_C = implies(B, C)
        a = A_implies_B.get_proof('a')
        b = B_implies_C.get_proof('b')
        x = A.get_proof('x')
        
        r = b(a(x)).abstract(x).abstract(b).abstract(a)
        
        outputs = {
            a: implies(A, B),
            b: implies(B, C),
            x: A,
            r: implies(implies(A, B), implies(implies(B,C), implies(A, C))),
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")
            
    def test_A_or_B_implies_C_iff_A_implies_C_and_B_implies_C(self):
        
        # iff forward
        #
        A_or_B_implies_C = implies(or_(A, B), C)
        y = A_or_B_implies_C.get_proof('y')
        x = A.get_proof('x')
        w = B.get_proof('w')
        
        r1 = ProofExpressionCombination(
            y(inl(x, B)).abstract(x), 
            y(inr(w, A)).abstract(w)
        ).abstract(y)
        
        outputs = {
            y: implies(or_(A, B), C),
            x: A,
            w: B,
            r1: implies(implies(or_(A, B), C), and_(implies(A,C), implies(B, C))),
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")        
        

        # iff backward
        #
        A_or_B = or_(A, B)
        A_implies_C_and_B_implies_C = and_(implies(A, C),implies(B, C))
        z = A_or_B.get_proof('z')
        p = A_implies_C_and_B_implies_C.get_proof('p')
        
        r2 = cases(z, p.select(0), p.select(1)).abstract(z).abstract(p)
        
        outputs = {
            z: or_(A, B),
            p: and_(implies(A, C),implies(B, C)),
            r2: implies(and_(implies(A,C), implies(B, C)), implies(or_(A, B), C)),
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")        
        

            
    