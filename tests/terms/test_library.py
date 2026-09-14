"""Computation rules of the standard library ([ST] ch. 4).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, Abs, Arrow, Const, Var, abstract
from symbolize.terms.eval import Evaluator
from symbolize.terms.library import (
    STANDARD,
    Falsum,
    N,
    Pi,
    Plus,
    Sigma,
    and_,
    apply,
    boolrec,
    cases,
    exists,
    false,
    forall,
    fst,
    ifthenelse,
    implies,
    inl,
    inr,
    lam,
    natrec,
    not_,
    numeral,
    or_,
    pair,
    snd,
    split,
    succ,
    true,
    when,
    zero,
)


class LibraryTest(unittest.TestCase):
    def setUp(self):
        self.ev = Evaluator(STANDARD)
        self.nf = self.ev.nf
        self.whnf = self.ev.whnf
        self.defeq = self.ev.defeq
        self.a, self.b, self.x, self.y = Var("a"), Var("b"), Var("x"), Var("y")
        self.A, self.B, self.C = Var("A"), Var("B"), Var("C")
        self.f = Var("f", Arrow(A0, A0))
        self.K = Const("K", Arrow(A0, A0))  # a family we never look inside


class TestPi(LibraryTest):
    def test_apply_lam(self):
        # apply(λ((x)f(x)), a) = f(a)     [ST] p80
        b = abstract(self.f(self.x), [self.x])
        self.assertEqual(self.nf(apply(lam(b), self.a)), self.f(self.a))

    def test_apply_is_stuck_on_variable(self):
        g = Var("g")
        self.assertEqual(self.whnf(apply(g, self.a)), apply(g, self.a))

    def test_abstract_then_apply_matches_old_test(self):
        # e.abstract(x).apply(a) computes to e[x := a]
        e = Var("e")
        self.assertEqual(self.nf(apply(lam(abstract(e, [self.x])), self.a)), e)


class TestSigma(LibraryTest):
    def test_fst_snd(self):
        p = pair(self.a, self.b)
        self.assertEqual(self.nf(fst(p)), self.a)
        self.assertEqual(self.nf(snd(p)), self.b)

    def test_split(self):
        p = pair(self.a, self.b)
        g = Const("g", Arrow(A0, A0))
        e = abstract(g(self.y), [self.x, self.y])
        self.assertEqual(self.nf(split(self.K, p, e)), g(self.b))

    def test_projections_stuck_on_variable(self):
        p = Var("p")
        self.assertEqual(self.whnf(fst(p)), fst(p))
        self.assertEqual(self.whnf(snd(fst(p))), snd(fst(p)))


class TestPlus(LibraryTest):
    def test_cases_inl_inr(self):
        # cases(inl(q), f, g) = f(q)     [ST] p81
        f, g, q, r = Var("f"), Var("g"), Var("q"), Var("r")
        self.assertEqual(self.nf(cases(inl(q), f, g)), apply(f, q))
        self.assertEqual(self.nf(cases(inr(r), f, g)), apply(g, r))

    def test_cases_reduces_branch(self):
        f = lam(abstract(succ(self.x), [self.x]))
        g = lam(abstract(zero, [self.x]))
        self.assertEqual(self.nf(cases(inl(zero), f, g)), succ(zero))
        self.assertEqual(self.nf(cases(inr(zero), f, g)), zero)

    def test_when(self):
        F = abstract(succ(self.x), [self.x])
        G = abstract(zero, [self.y])
        self.assertEqual(self.nf(when(self.K, inl(zero), F, G)), succ(zero))
        self.assertEqual(self.nf(when(self.K, inr(zero), F, G)), zero)


class TestBool(LibraryTest):
    def test_ifthenelse(self):
        c, d = Var("c"), Var("d")
        self.assertEqual(self.nf(ifthenelse(true, c, d)), c)
        self.assertEqual(self.nf(ifthenelse(false, c, d)), d)
        self.assertEqual(self.nf(boolrec(self.K, true, c, d)), c)
        self.assertEqual(self.nf(boolrec(self.K, false, c, d)), d)

    def test_stuck(self):
        b, c, d = Var("b"), Var("c"), Var("d")
        self.assertEqual(self.whnf(ifthenelse(b, c, d)), ifthenelse(b, c, d))


class TestNat(LibraryTest):
    def test_natrec_rules(self):
        n, c = Var("n"), Var("c")
        h = Const("h", Arrow(A0, A0))
        e = abstract(h(self.y), [self.x, self.y])
        self.assertEqual(self.nf(natrec(self.K, zero, c, e)), c)
        # one step on succ(n) then stuck on the variable n
        self.assertEqual(
            self.nf(natrec(self.K, succ(n), c, e)), h(natrec(self.K, n, c, e))
        )

    def test_addone(self):
        """[ST] p102: addone(2) = 3."""
        n, y = Var("n"), Var("y")
        step = abstract(succ(y), [n, y])
        body = natrec(self.K, self.x, succ(zero), step)
        addone = lam(abstract(body, [self.x]))
        self.assertEqual(self.nf(apply(addone, numeral(2))), numeral(3))

    def test_plus(self):
        m, n, y = Var("m"), Var("n"), Var("y")
        plus = lam(
            abstract(
                lam(
                    abstract(
                        natrec(self.K, n, m, abstract(succ(y), [self.x, y])),
                        [n],
                    )
                ),
                [m],
            )
        )

        def add(p, q):
            return apply(apply(plus, p), q)

        self.assertEqual(self.nf(add(numeral(2), numeral(3))), numeral(5))
        self.assertTrue(self.defeq(add(numeral(2), numeral(3)), numeral(5)))
        self.assertFalse(self.defeq(add(numeral(2), numeral(3)), numeral(4)))
        # addition on an open term reduces as far as the recursion allows
        self.assertEqual(self.nf(add(m, numeral(1))), succ(m))


class TestConnectives(LibraryTest):
    def test_unfold(self):
        A, B = self.A, self.B
        self.assertEqual(self.whnf(implies(A, B)), Pi(A, Abs((A0,), B)))
        self.assertEqual(self.whnf(and_(A, B)), Sigma(A, Abs((A0,), B)))
        self.assertEqual(self.whnf(or_(A, B)), Plus(A, B))
        self.assertEqual(self.whnf(not_(A)), Pi(A, Abs((A0,), Falsum)))
        P = Var("P", Arrow(A0, A0))
        self.assertEqual(self.whnf(forall(N, P)), Pi(N, P))
        self.assertEqual(self.whnf(exists(N, P)), Sigma(N, P))

    def test_connectives_are_definitionally_equal_to_their_unfolding(self):
        A, B = self.A, self.B
        self.assertTrue(self.defeq(implies(A, B), Pi(A, abstract(B, [self.x]))))
        self.assertTrue(self.defeq(not_(A), implies(A, Falsum)))
        self.assertFalse(self.defeq(implies(A, B), implies(B, A)))
        # ∀ over a constant family is ⇒
        self.assertTrue(self.defeq(forall(A, abstract(B, [self.x])), implies(A, B)))

    def test_signatures_registered(self):
        for c in (implies, and_, or_, not_, forall, exists):
            self.assertIsNotNone(STANDARD.signature(c))
            self.assertIsNotNone(STANDARD.definition(c))
        self.assertTrue(STANDARD.is_constructor(succ))
        self.assertTrue(STANDARD.is_constructor(pair))
        self.assertFalse(STANDARD.is_constructor(fst))
        self.assertEqual(STANDARD.constructor_of(inl), Plus)


if __name__ == "__main__":
    unittest.main()
