"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.expressions.arity import ArityArrow, A0
from symbolize.logic.typetheory.proposition import and_, implies, or_, forall, exists
from symbolize.logic.typetheory.proof import (
    ProofExpressionCombination,
    ProofExpression,
    fst,
    snd,
    inl,
    inr,
    cases,
    Fst,
    Snd,
)
from symbolize.logic.typetheory.boolean import bool_, True_, False_, ifthenelse
from symbolize.logic.typetheory.variables import A, B, C
from symbolize.logic.typetheory.proposition import PropositionSymbol


class TestDeductionRules(unittest.TestCase):
    def test_conjunction_introduction(self):
        p = A.get_proof("p")
        q = B.get_proof("q")

        r = ProofExpressionCombination(p, q)

        self.assertIsInstance(r, ProofExpression)
        self.assertEqual(r.proposition_type, and_(A, B))

    def test_conjunction_elimination(self):
        p = A.get_proof("p")
        q = B.get_proof("q")

        # test constructed conjunction
        r1 = ProofExpressionCombination(p, q)

        s11 = fst(r1)
        s12 = snd(r1)

        self.assertIsInstance(s11, ProofExpression)
        self.assertIsInstance(s12, ProofExpression)

        self.assertEqual(s11.proposition_type, A)
        self.assertEqual(s12.proposition_type, B)

        # test given conjunction
        A_and_B = and_(A, B)
        r2 = A_and_B.get_proof("s2")  # , arity=ArityCross(A0,A0))
        s21 = fst(r2)
        s22 = snd(r2)

        self.assertIsInstance(s21, ProofExpression)
        self.assertIsInstance(s22, ProofExpression)

        self.assertEqual(s21.proposition_type, A)
        self.assertEqual(s22.proposition_type, B)

    def test_implication_introduction(self):
        x = A.get_proof("x")
        e = B.get_proof("e")

        r = e.abstract(x)

        self.assertIsInstance(r, ProofExpression)
        self.assertEqual(r.proposition_type, implies(A, B))

    def test_implication_elimination(self):
        a = A.get_proof("a")

        # test contructed implication
        x = A.get_proof("x")
        e = B.get_proof("e")
        r1 = e.abstract(x)

        s1 = r1.apply(a)
        self.assertIsInstance(s1, ProofExpression)
        self.assertEqual(s1.proposition_type, B)

        # test give implication
        A_implies_B = implies(A, B)
        r2 = A_implies_B.get_proof("r2")  # , arity=ArityArrow(A0,A0))

        s2 = r2.apply(a)
        self.assertIsInstance(s2, ProofExpression)
        self.assertEqual(s2.proposition_type, B)

    def test_disjunction_introduction(self):
        q = A.get_proof("q")
        r = B.get_proof("r")

        s1 = inl(q, inject_proposition=B)

        self.assertIsInstance(s1, ProofExpression)
        self.assertEqual(s1.proposition_type, or_(A, B))

        s2 = inr(r, inject_proposition=A)

        self.assertIsInstance(s2, ProofExpression)
        self.assertEqual(s2.proposition_type, or_(A, B))

    def test_disjunction_elimination(self):

        A_implies_C = implies(A, C)
        B_implies_C = implies(B, C)

        f = A_implies_C.get_proof("f")
        g = B_implies_C.get_proof("g")

        # test constructed disjunction
        q = A.get_proof("q")
        r = B.get_proof("r")

        p1 = inl(q, inject_proposition=B)
        p2 = inr(r, inject_proposition=A)

        s1 = cases(p1, f, g)
        self.assertIsInstance(s1, ProofExpression)
        self.assertEqual(s1.proposition_type, C)

        s2 = cases(p2, f, g)
        self.assertIsInstance(s2, ProofExpression)
        self.assertEqual(s2.proposition_type, C)

        # test given disjunction
        A_or_B = or_(A, B)
        p3 = A_or_B.get_proof("p3")

        s3 = cases(p3, f, g)
        self.assertIsInstance(s3, ProofExpression)
        self.assertEqual(s3.proposition_type, C)

    def test_universal_quantifier_introduction(self):
        x = A.get_proof("x")
        P = PropositionSymbol("P", assume_contains=[x], arity=ArityArrow(A0, A0))
        p = P.get_proof("p")

        r = p.abstract(x)

        self.assertIsInstance(r, ProofExpression)
        self.assertEqual(r.proposition_type, forall(x, P))

    def test_universal_quantifier_elimination(self):
        a = A.get_proof("a")
        x = A.get_proof("x")
        P = PropositionSymbol("P", assume_contains=[x], arity=ArityArrow(A0, A0))
        p = P.get_proof("p")

        # test contructed quantification
        r1 = p.abstract(x)

        s1 = r1.apply(a)

        self.assertIsInstance(s1, ProofExpression)
        self.assertEqual(
            s1.proposition_type, P.substitute(x, a))

        # TODO: test constructed quantification with P actually
        # containing x.

        # test given quantification
        forall_x_P = forall(x, P)
        r2 = forall_x_P.get_proof("f")

        s2 = r2.apply(a)

        self.assertIsInstance(s2, ProofExpression)
        self.assertEqual(s2.proposition_type, P.substitute(x, a))

    def test_existential_quantifier_introduction(self):
        a = A.get_proof("a")
        x = A.get_proof("x")
        P = PropositionSymbol("P", assume_contains=[x])
        P1 = P.substitute(x, a)
        p = P1.get_proof("p")

        r = ProofExpressionCombination(a, p)

        self.assertIsInstance(r, ProofExpression)
        self.assertEqual(r.proposition_type, exists(x, P))

    @unittest.skip("needs fixing")
    def test_existential_quantifier_elimination(self):
        x = A.get_proof("x")
        P = PropositionSymbol("P", assume_contains=[x])

        # test constructed quantification
        prop = exists(x, P)
        p = prop.get_proof("p")

        s11 = Fst(p)
        s12 = Snd(p)

        self.assertIsInstance(s11, ProofExpression)
        self.assertIsInstance(s12, ProofExpression)

        self.assertEqual(s11.proposition_type, A)
        self.assertEqual(s12.proposition_type, P)

        # TODO: test constructed quantification with P actually
        # containing x.

        # test given quantification
        exists_x_P = exists(x, P)
        r2 = exists_x_P.get_proof("f")

        s21 = Fst(r2)
        s22 = Snd(r2)

        self.assertIsInstance(s21, ProofExpression)
        self.assertIsInstance(s22, ProofExpression)

        self.assertEqual(s21.proposition_type, A)
        self.assertEqual(s22.proposition_type, P)

    def test_boolean_introduction(self):

        outputs = {True_: bool_, False_: bool_}

        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression)
            self.assertEqual(_p.proposition_type, _t)

    def test_boolean_elimination(self):

        C = PropositionSymbol("C")
        c = C.get_proof("c")
        d = C.get_proof("d")
        tr = bool_.get_proof("tr")

        r = ifthenelse(tr, c, d)

        outputs = {tr: bool_, r: C}

        for _p, _t in outputs.items():
            self.assertIsInstance(_p, ProofExpression)
            self.assertEqual(_p.proposition_type, _t)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
