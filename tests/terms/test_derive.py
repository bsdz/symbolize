"""Natural-deduction derivations on judgements, ported from
tests/logic/typetheory/{test_deduction_rules,test_examples,test_natural,
test_computation}.py.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms.check import TypingError
from symbolize.terms.decl import SET
from symbolize.terms.derive import (Argument, DerivationError, Judgement,
                                    abort, and_, cases, exists, family, forall,
                                    hyp, ifthenelse, implies, inl, inr, judge,
                                    natrec, not_, or_, pair, prim, set_var)
from symbolize.terms.library import (Bool, Falsum, N, false, numeral, succ,
                                     true, zero)


class DeriveTest(unittest.TestCase):
    def setUp(self):
        self.A, self.B, self.C = set_var("A"), set_var("B"), set_var("C")
        self.N = judge(N, SET)
        self.Bool = judge(Bool, SET)

    def assertType(self, j, type_):
        self.assertIsInstance(j, Judgement)
        self.assertTrue(j.has_type(type_), "%r, expected type %r" % (j, type_))


class TestHypotheses(DeriveTest):
    def test_set_var_and_hyp(self):
        A = self.A
        self.assertTrue(A.is_set)
        x = hyp("x", A)
        self.assertTrue(x.is_hypothesis)
        self.assertType(x, A)
        self.assertEqual(repr(x), "x : A")
        self.assertEqual(A.hyp("y").type, A.term)
        with self.assertRaises(DerivationError):
            hyp("x", x)  # x is not a set

    def test_family(self):
        P = family("P", self.N)
        self.assertTrue(P.is_family)
        n = hyp("n", self.N)
        self.assertTrue(P(n).is_set)
        self.assertTrue(P(n).ctx.lookup(n.term) is not None)
        with self.assertRaises(TypingError):
            P(hyp("b", self.Bool))
        self.assertEqual(repr(P), "P(z) set [z ∈ N]")

    def test_connectives_form_sets(self):
        A, B = self.A, self.B
        for s in (
            A >> B,
            A & B,
            A | B,
            ~A,
            implies(A, B),
            and_(A, B),
            or_(A, B),
            not_(A),
        ):
            self.assertTrue(s.is_set)
        self.assertEqual((A >> B).term, implies(A, B).term)
        with self.assertRaises(DerivationError):
            implies(A, hyp("x", A))

    def test_quantifiers_form_sets(self):
        x = hyp("x", self.N)
        P = family("P", self.N)
        s1 = forall(x, P(x))
        s2 = exists(x, P(x))
        self.assertTrue(s1.is_set and s2.is_set)
        self.assertNotIn(x.term, s1.ctx)  # x is bound, not a hypothesis
        # the family form is the same set up to eta
        self.assertTrue(forall(self.N, P).defeq(s1))
        self.assertTrue(exists(self.N, P).defeq(s2))
        self.assertNotEqual(forall(self.N, P).term, s1.term)


class TestDeductionRules(DeriveTest):
    """tests/logic/typetheory/test_deduction_rules.py"""

    def test_conjunction_introduction(self):
        p, q = hyp("p", self.A), hyp("q", self.B)
        r = pair(p, q)
        self.assertType(r, self.A & self.B)
        self.assertType(p.pair(q), and_(self.A, self.B))

    def test_conjunction_elimination(self):
        A, B = self.A, self.B
        p, q = hyp("p", A), hyp("q", B)
        r1 = pair(p, q)
        self.assertType(r1.fst, A)
        self.assertType(r1.snd, B)
        r2 = hyp("s2", A & B)
        self.assertType(r2.fst, A)
        self.assertType(r2.snd, B)
        with self.assertRaises(DerivationError):
            p.fst

    def test_implication_introduction(self):
        x, e = hyp("x", self.A), hyp("e", self.B)
        r = e.abstract(x)
        self.assertType(r, self.A >> self.B)
        self.assertNotIn(x.term, r.ctx)  # discharged
        self.assertIn(e.term, r.ctx)

    def test_implication_elimination(self):
        A, B = self.A, self.B
        a, x, e = hyp("a", A), hyp("x", A), hyp("e", B)
        r1 = e.abstract(x)
        self.assertType(r1(a), B)
        r2 = hyp("r2", A >> B)
        self.assertType(r2(a), B)
        with self.assertRaises(DerivationError):
            r2(e)  # e : B, not A
        with self.assertRaises(DerivationError):
            a(x)  # a is not a function

    def test_disjunction_introduction(self):
        A, B = self.A, self.B
        q, r = hyp("q", A), hyp("r", B)
        self.assertType(inl(q, B), A | B)
        self.assertType(inr(r, A), A | B)
        self.assertType(q.inl(B), or_(A, B))

    def test_disjunction_elimination(self):
        A, B, C = self.A, self.B, self.C
        f, g = hyp("f", A >> C), hyp("g", B >> C)
        q, r = hyp("q", A), hyp("r", B)
        self.assertType(cases(inl(q, B), f, g), C)
        self.assertType(cases(inr(r, A), f, g), C)
        p3 = hyp("p3", A | B)
        self.assertType(p3.cases(f, g), C)
        with self.assertRaises(DerivationError):
            cases(p3, g, f)

    def test_universal_quantifier_introduction(self):
        x = hyp("x", self.A)
        P = family("P", self.A)
        f = hyp("f", forall(x, P(x)))
        r = f(x).abstract(x)  # eta-expansion of f
        self.assertType(r, forall(x, P(x)))
        self.assertType(r, forall(self.A, P))
        # a hypothesis p : P(x) cannot be generalised over x ([ST] p89:
        # x must not be free in any undischarged assumption)
        p = hyp("p", P(x))
        with self.assertRaises(DerivationError):
            p.abstract(x)

    def test_universal_quantifier_elimination(self):
        a, x = hyp("a", self.A), hyp("x", self.A)
        P = family("P", self.A)
        r2 = hyp("f", forall(x, P(x)))
        r1 = r2(x).abstract(x)
        self.assertType(r1(a), P(a))
        self.assertType(r2(a), P(a))
        self.assertType(r2(x), P(x))

    def test_existential_quantifier_introduction(self):
        a, x = hyp("a", self.A), hyp("x", self.A)
        P = family("P", self.A)
        p = hyp("p", P(a))
        r = pair(a, p)
        self.assertType(r, exists(x, P(x)))
        self.assertType(r, exists(self.A, P))
        # an explicit family when the witness is not a variable
        n = numeral(2)
        Q = family("Q", self.N)
        q = hyp("q", Q(judge(n, N)))
        r2 = pair(judge(n, N), q, family=Q.term)
        self.assertType(r2, exists(self.N, Q))

    def test_existential_quantifier_elimination(self):
        x = hyp("x", self.A)
        P = family("P", self.A)
        p = hyp("p", exists(x, P(x)))
        self.assertType(p.fst, self.A)
        self.assertType(p.snd, P(p.fst))

    def test_boolean(self):
        C = self.C
        c, d = hyp("c", C), hyp("d", C)
        tr = hyp("tr", self.Bool)
        self.assertType(judge(true, Bool), self.Bool)
        self.assertType(ifthenelse(tr, c, d), C)
        with self.assertRaises(DerivationError):
            ifthenelse(c, c, d)

    def test_falsum(self):
        f, a = hyp("f", ~self.A), hyp("a", self.A)
        bottom = f(a)
        self.assertType(bottom, judge(Falsum, SET))
        self.assertType(abort(bottom, self.B), self.B)
        self.assertType(bottom.abort(self.C), self.C)


class TestExamples(DeriveTest):
    """tests/logic/typetheory/test_examples.py"""

    def test_A_and_B_deduce_B_and_A(self):
        """[ST] p72"""
        p, q = hyp("p", self.A), hyp("q", self.B)
        r1 = pair(p, q)
        r2 = pair(r1.snd, r1.fst)
        self.assertType(r1, self.A & self.B)
        self.assertType(r2, self.B & self.A)
        # and the proof computes
        self.assertEqual(r2.run().term, pair(q, p).term)

    def test_identity(self):
        """[ST] p83"""
        x = hyp("x", self.A)
        self.assertType(x.abstract(x), self.A >> self.A)

    def test_A_implies_B_implies_C_both_imply_A_implies_C(self):
        """[ST] p83-84 -- the README example"""
        A, B, C = self.A, self.B, self.C
        a, b, x = hyp("a", A >> B), hyp("b", B >> C), hyp("x", A)
        r = b(a(x)).abstract(x).abstract(b).abstract(a)
        self.assertType(r, (A >> B) >> ((B >> C) >> (A >> C)))
        self.assertEqual(len(r.ctx), 3)  # only A, B, C remain
        self.assertEqual(r, b(a(x)).abstract(a, b, x))

    def test_A_or_B_implies_C_iff_A_implies_C_and_B_implies_C(self):
        A, B, C = self.A, self.B, self.C
        # forward
        y, x, w = hyp("y", (A | B) >> C), hyp("x", A), hyp("w", B)
        r1 = pair(y(inl(x, B)).abstract(x), y(inr(w, A)).abstract(w)).abstract(y)
        self.assertType(r1, ((A | B) >> C) >> ((A >> C) & (B >> C)))
        # backward
        z, p = hyp("z", A | B), hyp("p", (A >> C) & (B >> C))
        r2 = cases(z, p.fst, p.snd).abstract(z).abstract(p)
        self.assertType(r2, ((A >> C) & (B >> C)) >> ((A | B) >> C))

    def test_forall_x_B_implies_C_forall_x_B_both_imply_forall_x_C(self):
        """[ST] p92"""
        A = self.A
        x = hyp("x", A)
        B, C = family("B", A), family("C", A)
        r = hyp("r", forall(x, B(x) >> C(x)))
        p = hyp("p", forall(x, B(x)))
        s = r(x)(p(x)).abstract(x)
        self.assertType(s, forall(x, C(x)))
        s1 = s.abstract(p).abstract(r)
        self.assertType(
            s1, forall(x, B(x) >> C(x)) >> (forall(x, B(x)) >> forall(x, C(x)))
        )

    def test_exists_x_P_implies_Q_deduce_forall_x_P_implies_Q(self):
        """[ST] p93"""
        X, Q = set_var("X"), set_var("Q")
        x = hyp("x", X)
        P = family("P", X)
        p = hyp("p", P(x))
        # forwards
        e = hyp("e", exists(x, P(x)) >> Q)
        r1 = e(pair(x, p)).abstract(p).abstract(x)
        self.assertType(r1, forall(x, P(x) >> Q))
        # backwards
        e2 = hyp("e", forall(x, P(x) >> Q))
        p2 = hyp("p", exists(x, P(x)))
        r2 = e2(p2.fst)(p2.snd).abstract(p2)
        self.assertType(r2, exists(x, P(x)) >> Q)

    def test_discharge_order_matters(self):
        x = hyp("x", self.A)
        P = family("P", self.A)
        p = hyp("p", P(x))
        with self.assertRaises(DerivationError):
            p.abstract(x)  # p's type depends on x; discharge p first
        self.assertType(p.abstract(p).abstract(x), forall(x, P(x) >> P(x)))


class TestNatural(DeriveTest):
    """tests/logic/typetheory/test_natural.py and the addone example"""

    def test_natural_introduction(self):
        self.assertType(judge(zero, N), self.N)
        self.assertType(judge(succ(zero), N), self.N)

    def test_natural_elimination(self):
        n = hyp("n", self.N)
        C = family("C", self.N)
        c = hyp("c", C(judge(zero, N)))
        x = hyp("x", self.N)
        f = hyp("f", forall(x, C(x) >> C(judge(succ(x.term), N, x.ctx))))
        r = prim(n, c, f)
        self.assertType(r, C(n))
        # motive inferred from f
        self.assertEqual(natrec(n, c, f), r)
        with self.assertRaises(DerivationError):
            prim(c, c, f)  # c is not a natural number

    def test_prim_succ(self):
        """test_computation.test_prim_succ"""
        n = hyp("n", self.N)
        C = set_var("C")  # a constant family
        c, h = hyp("c", C), hyp("h", C)
        f = h.abstract(h).abstract(n)  # λn.λh.h : ∀n.(C ⇒ C)
        r1 = prim(judge(zero, N), c, f)
        r2 = prim(judge(succ(n.term), N, n.ctx), c, f)
        self.assertType(r1, C)
        self.assertType(r2, C)
        self.assertEqual(r1.run().term, c.term)
        self.assertEqual(r2.run().term, prim(n, c, f).run().term)

    def test_addone(self):
        """[ST] p102"""
        x, y, n = hyp("x", self.N), hyp("y", self.N), hyp("n", self.N)
        f = judge(succ(y.term), N, y.ctx).abstract(y).abstract(n)
        one = judge(succ(zero), N)
        addone = prim(x, one, f).abstract(x)
        self.assertType(addone, self.N >> self.N)
        two = judge(numeral(2), N)
        r = addone(two)
        self.assertType(r, self.N)
        self.assertEqual(r.run().term, numeral(3))


class TestComputation(DeriveTest):
    """tests/logic/typetheory/test_computation.py"""

    def test_fst_snd(self):
        p, q = hyp("p", self.A), hyp("q", self.B)
        self.assertEqual(pair(p, q).fst.run().term, p.term)
        self.assertEqual(pair(p, q).snd.run().term, q.term)

    def test_abstract(self):
        x, e, a = hyp("x", self.A), hyp("e", self.B), hyp("a", self.A)
        r = e.abstract(x)(a)
        self.assertEqual(r.run().term, e.term)
        # with a genuine dependency on x
        P = family("P", self.A)
        f = hyp("f", forall(x, P(x)))
        s = f(x).abstract(x)(a)
        self.assertEqual(s.run().term, f(a).term)
        self.assertEqual(s.run().term, f(x).subst(x, a).term)

    def test_cases_inl_inr(self):
        A, B, C = self.A, self.B, self.C
        f, g = hyp("f", A >> C), hyp("g", B >> C)
        q, r = hyp("q", A), hyp("r", B)
        self.assertEqual(cases(inl(q, B), f, g).run().term, f(q).term)
        self.assertEqual(cases(inr(r, A), f, g).run().term, g(r).term)

    def test_ifthenelse(self):
        c, d = hyp("c", self.C), hyp("d", self.C)
        T, F = judge(true, Bool), judge(false, Bool)
        self.assertEqual(ifthenelse(T, c, d).run().term, c.term)
        self.assertEqual(ifthenelse(F, c, d).run().term, d.term)

    def test_substitution(self):
        x = hyp("x", self.A)
        P = family("P", self.A)
        p = hyp("p", P(x))
        a = hyp("a", self.A)
        s = p.subst(x, a)
        self.assertType(s, P(a))
        self.assertNotIn(x.term, s.ctx)
        self.assertEqual(s.term, p.term)


class TestOldSpellings(DeriveTest):
    def test_aliases(self):
        A, B = self.A, self.B
        x = A.get_proof("x")
        f = (A >> B).get_proof("f")
        self.assertEqual(f.apply(x), f(x))
        p = (A & B).get_proof("p")
        self.assertEqual(p.select(0), p.fst)
        self.assertEqual(p.select(1), p.snd)


class TestArgument(DeriveTest):
    def test_tree(self):
        A, B = self.A, self.B
        x, a = hyp("x", A), hyp("a", A >> B)
        arg1 = Argument([x, a], a(x), label="⇒E")
        arg2 = Argument([arg1], a(x).abstract(x), discharges=[x], label="⇒I")
        self.assertEqual(arg2.leaves, (x, a))
        self.assertIn("⇒I", repr(arg2))
        self.assertIn("a(x) : B", repr(arg1))


if __name__ == "__main__":
    unittest.main()
