'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest

from symbolize.expressions.arity import A0, ArityArrow
from symbolize.logic.typetheory.proposition import and_, implies, or_, forall, exists
from symbolize.logic.typetheory.proof import ProofExpressionCombination, ProofExpression, fst, snd, inl, inr, cases, Fst, Snd
from symbolize.logic.typetheory.natural import N, prim, succ, zero
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
            y(inl(x, inject_proposition=B)).abstract(x), 
            y(inr(w, inject_proposition=A)).abstract(w)
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
        

    def test_forall_x_B_implies_C_forall_x_B_both_imply_forall_x_C(self):
        """ [ST] p92 """
        
        x = A.get_proof('x')
        B = PropositionSymbol('B', assume_contains=[x])
        C = PropositionSymbol('C', assume_contains=[x])
        B_implies_C = implies(B, C)
        
        Forall_x_B_implies_C = forall(x, B_implies_C)
        r = Forall_x_B_implies_C.get_proof('r')
        Forall_x_B = forall(x, B)
        p = Forall_x_B.get_proof('p')
        
        s = r(x)(p(x)).abstract(x)
        s1 = s.abstract(p).abstract(r)
        
        outputs = {
            x: A,
            r: forall(x, B_implies_C),
            p: forall(x, B),
            s: forall(x, C),
            s1: implies(forall(x, B_implies_C), implies(forall(x, B), forall(x, C)))
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")
            
    def test_exists_x_P_implies_Q_deduce_forall_x_P_implies_Q(self):
        """ [ST] p93 """
        
        X = PropositionSymbol('X')
        x = X.get_proof('x')
        P = PropositionSymbol('P', assume_contains=[x]).substitute(x, x) # todo: kludge!
        p = P.get_proof('p')
        Q = PropositionSymbol('Q')

        # forwards iff
        #
        Exists_x_P_implies_Q = implies(exists(x, P), Q)
        e = Exists_x_P_implies_Q.get_proof('e')
        
        r1 = e(ProofExpressionCombination(x,p)).abstract(p).abstract(x)
        
        outputs = {
            e: implies(exists(x, P), Q),
            r1: forall(x,implies(P,Q, target_arity=ArityArrow(A0,A0))), # todo: do we need to force arity?
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")           
    
        # backwards iff
        #
        Forall_x_P_implies_Q = forall(x,implies(P,Q, target_arity=ArityArrow(A0,A0)))
        e = Forall_x_P_implies_Q.get_proof('e')
        Exists_x_P = exists(x, P)
        p = Exists_x_P.get_proof('p')
        
        r2 = e(Fst(p))(Snd(p)).abstract(p)
        
        outputs = {
            r2: implies(exists(x, P), Q),
            e: forall(x,implies(P,Q)),
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")
    
    @unittest.skip("needs work")
    def test_addone(self):
        """ [ST] p102 """

        x = N.get_proof('x')
        y = N.get_proof('y')
        n = N.get_proof('n')
        
        f = succ(y).abstract(y).abstract(n)
        addone = prim(x, succ(zero), f).abstract(x)
        
        two = succ(succ(zero))
        
        r1 = addone(two)
        r2 = r1.run()
        self.assertEqual(r2, prim(succ(succ(zero)), succ(zero), f))
        r3 = r2.run()
        
        pass
        