'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2018  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''
import unittest

from symbolize.logic.typetheory.proposition import implies, forall
from symbolize.logic.typetheory.proof import ProofExpression
from symbolize.logic.typetheory.proposition import PropositionSymbol
from symbolize.logic.typetheory.natural import N, zero, succ, prim

class TestNaturalNumbers(unittest.TestCase):


    def test_natural_introduction(self):
        
        outputs = {
            zero: N,
            succ(zero): N,
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")      
    
    def test_natural_elimination(self):
        
        n = N.get_proof('n')
        C = PropositionSymbol('C', assume_contains=[n])
        c = C.get_proof('c')
        
        
        Forall_n_C_implies_C = forall(n, implies(C, C))
        f = Forall_n_C_implies_C.get_proof('f')
        
        r = prim(n, c, f)
        
        outputs = {
            r: C,
        }
        
        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression, "result is a proof")
            self.assertEqual(_p.proposition_type, _t, "proof has correct expr")  


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()