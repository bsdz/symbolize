"""Typing rules of the standard library ([ST] ch. 4, [BN]).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, Abs, Arrow, Const, Cross, Var, abstract
from symbolize.terms.check import Checker, Context, TypingError
from symbolize.terms.decl import SET
from symbolize.terms.library import (STANDARD, Bool, Falsum, N, Pi, Plus,
                                     Sigma, abort, and_, apply, boolrec, cases,
                                     exists, false, forall, fst, ifthenelse,
                                     implies, inl, inr, lam, natrec, not_,
                                     numeral, or_, pair, snd, split, succ,
                                     true, when, zero)


def const_family(body):
    return Abs((A0,), body, hints=("_",))


class CheckerTest(unittest.TestCase):
    def setUp(self):
        self.checker = Checker(STANDARD)
        self.infer = self.checker.infer
        self.check = self.checker.check
        self.is_set = self.checker.is_set
        self.A, self.B, self.C = Var("A"), Var("B"), Var("C")
        self.x, self.y, self.z = Var("x"), Var("y"), Var("z")
        self.sets = (
            Context().extend(self.A, SET).extend(self.B, SET).extend(self.C, SET)
        )

    def assertType(self, ctx, term, type):
        self.assertTrue(
            self.checker.defeq(self.infer(ctx, term), type),
            "%r : %r, expected %r" % (term, self.infer(ctx, term), type),
        )
        self.check(ctx, term, type)  # and checking mode agrees


class TestFormation(CheckerTest):
    def test_sets(self):
        A, B = self.A, self.B
        for t in (
            A,
            N,
            Bool,
            Falsum,
            Pi(A, const_family(B)),
            Sigma(A, const_family(B)),
            Plus(A, B),
            implies(A, B),
            and_(A, B),
            or_(A, B),
            not_(A),
            forall(N, const_family(A)),
            exists(A, const_family(B)),
            implies(implies(A, B), implies(not_(B), not_(A))),
        ):
            self.assertEqual(self.infer(self.sets, t), SET, t)
            self.is_set(self.sets, t)

    def test_family(self):
        P = Var("P", Arrow(A0, A0))
        ctx = self.sets.extend(P, SET, hyps=[(self.z, N)])
        self.assertEqual(self.infer(ctx, P(zero)), SET)
        self.assertEqual(self.infer(ctx, forall(N, P)), SET)
        self.assertEqual(self.infer(ctx, exists(N, P)), SET)
        self.assertEqual(
            self.infer(
                ctx, forall(N, abstract(implies(P(self.x), P(succ(self.x))), [self.x]))
            ),
            SET,
        )
        with self.assertRaises(TypingError):
            self.infer(ctx, P(true))  # Bool is not N
        with self.assertRaises(TypingError):
            self.infer(ctx, forall(Bool, P))

    def test_not_sets(self):
        with self.assertRaises(TypingError):
            self.infer(self.sets, SET)
        with self.assertRaises(TypingError):
            self.is_set(self.sets, zero)
        with self.assertRaises(TypingError):
            self.is_set(self.sets, Var("D"))  # not in context
        with self.assertRaises(TypingError):
            self.is_set(self.sets, Pi(zero, const_family(self.A)))


class TestPi(CheckerTest):
    def test_introduction(self):
        A, B, x = self.A, self.B, self.x
        # λx.x ∈ A ⇒ A
        self.check(self.sets, lam(abstract(x, [x])), implies(A, A))
        with self.assertRaises(TypingError):
            self.check(self.sets, lam(abstract(x, [x])), implies(A, B))
        # λ cannot be inferred without an expected type
        with self.assertRaises(TypingError):
            self.infer(self.sets, lam(abstract(x, [x])))

    def test_elimination(self):
        A, B = self.A, self.B
        f, a = Var("f"), Var("a")
        ctx = self.sets.extend(f, implies(A, B)).extend(a, A)
        self.assertType(ctx, apply(f, a), B)
        with self.assertRaises(TypingError):
            self.infer(ctx, apply(a, f))
        with self.assertRaises(TypingError):
            self.infer(ctx, apply(f, f))

    def test_forall(self):
        P = Var("P", Arrow(A0, A0))
        f, n = Var("f"), Var("n")
        ctx = self.sets.extend(P, SET, hyps=[(self.z, N)])
        ctx = ctx.extend(f, forall(N, P)).extend(n, N)
        self.assertType(ctx, apply(f, n), P(n))
        self.assertType(ctx, apply(f, succ(n)), P(succ(n)))
        # ∀-introduction: λn.f(n) ∈ ∀n.P(n)
        self.check(ctx, lam(abstract(apply(f, n), [n])), forall(N, P))
        with self.assertRaises(TypingError):
            self.check(
                ctx, lam(abstract(apply(f, n), [n])), forall(N, const_family(P(zero)))
            )

    def test_readme_example(self):
        """(A ⇒ B) ⇒ ((B ⇒ C) ⇒ (A ⇒ C))"""
        A, B, C = self.A, self.B, self.C
        a, b, x = Var("a"), Var("b"), Var("x")
        ctx = self.sets.extend(a, implies(A, B)).extend(b, implies(B, C)).extend(x, A)
        self.assertType(ctx, apply(a, x), B)
        self.assertType(ctx, apply(b, apply(a, x)), C)
        body = apply(b, apply(a, x))
        proof = lam(abstract(lam(abstract(lam(abstract(body, [x])), [b])), [a]))
        self.check(
            self.sets,
            proof,
            implies(implies(A, B), implies(implies(B, C), implies(A, C))),
        )
        with self.assertRaises(TypingError):
            self.check(
                self.sets,
                proof,
                implies(implies(A, B), implies(implies(B, C), implies(C, A))),
            )


class TestSigma(CheckerTest):
    def test_and(self):
        A, B = self.A, self.B
        a, b, p = Var("a"), Var("b"), Var("p")
        ctx = self.sets.extend(a, A).extend(b, B).extend(p, and_(A, B))
        self.check(ctx, pair(a, b), and_(A, B))
        with self.assertRaises(TypingError):
            self.check(ctx, pair(b, a), and_(A, B))
        with self.assertRaises(TypingError):
            self.infer(ctx, pair(a, b))  # B(a) not determined
        self.assertType(ctx, fst(p), A)
        self.assertType(ctx, snd(p), B)
        # a bare pair is not inferable, so neither is a projection of one;
        # the derivation layer supplies the type (see derive.py)
        with self.assertRaises(TypingError):
            self.infer(ctx, fst(pair(a, b)))

    def test_exists(self):
        P = Var("P", Arrow(A0, A0))
        a, q, p = Var("a"), Var("q"), Var("p")
        ctx = self.sets.extend(P, SET, hyps=[(self.z, N)])
        ctx = ctx.extend(a, N).extend(q, P(a)).extend(p, exists(N, P))
        self.check(ctx, pair(a, q), exists(N, P))
        self.assertType(ctx, fst(p), N)
        self.assertType(ctx, snd(p), P(fst(p)))
        self.assertType(ctx, snd(pair(a, q)), P(a))
        with self.assertRaises(TypingError):
            self.check(ctx, pair(succ(a), q), exists(N, P))  # q ∉ P(succ(a))

    def test_split(self):
        A, B = self.A, self.B
        p = Var("p")
        K = Var("K", Arrow(A0, A0))
        ctx = self.sets.extend(p, and_(A, B))
        ctx = ctx.extend(K, SET, hyps=[(self.z, and_(A, B))])
        x, y = self.x, self.y
        # e(x, y) ∈ K(pair(x, y)) [x ∈ A, y ∈ B] -- given by hypothesis h
        h = Var("h", Arrow(Cross((A0, A0)), A0))
        hx = Var("hx")
        ctx = ctx.extend(h, K(pair(hx, self.z)), hyps=[(hx, A), (self.z, B)])
        e = abstract(h(x, y), [x, y])
        self.assertType(ctx, split(K, p, e), K(p))
        with self.assertRaises(TypingError):
            self.infer(ctx, split(K, p, abstract(h(y, x), [x, y])))


class TestPlus(CheckerTest):
    def test_or(self):
        A, B, C = self.A, self.B, self.C
        a, b, p = Var("a"), Var("b"), Var("p")
        f, g = Var("f"), Var("g")
        ctx = self.sets.extend(a, A).extend(b, B).extend(p, or_(A, B))
        ctx = ctx.extend(f, implies(A, C)).extend(g, implies(B, C))
        self.check(ctx, inl(a), or_(A, B))
        self.check(ctx, inr(b), or_(A, B))
        with self.assertRaises(TypingError):
            self.check(ctx, inl(b), or_(A, B))
        with self.assertRaises(TypingError):
            self.infer(ctx, inl(a))
        self.assertType(ctx, cases(p, f, g), C)
        self.assertType(ctx, cases(inl(a), f, g), C)
        with self.assertRaises(TypingError):
            self.infer(ctx, cases(p, g, f))

    def test_when(self):
        A, B = self.A, self.B
        p = Var("p")
        K = Var("K", Arrow(A0, A0))
        ctx = self.sets.extend(p, or_(A, B)).extend(K, SET, hyps=[(self.z, or_(A, B))])
        F, G = Var("F", Arrow(A0, A0)), Var("G", Arrow(A0, A0))
        ctx = ctx.extend(F, K(inl(self.x)), hyps=[(self.x, A)])
        ctx = ctx.extend(G, K(inr(self.y)), hyps=[(self.y, B)])
        self.assertType(ctx, when(K, p, F, G), K(p))
        with self.assertRaises(TypingError):
            self.infer(ctx, when(K, p, G, F))


class TestFalsum(CheckerTest):
    def test_abort_and_not(self):
        A, a, f, p = self.A, Var("a"), Var("f"), Var("p")
        ctx = self.sets.extend(a, A).extend(f, not_(A)).extend(p, Falsum)
        self.assertType(ctx, apply(f, a), Falsum)
        self.assertType(ctx, abort(A, p), A)
        self.assertType(ctx, abort(self.B, apply(f, a)), self.B)
        # ¬¬A from A:  λg. g(a) ∈ ¬¬A
        g = Var("g")
        self.check(ctx, lam(abstract(apply(g, a), [g])), not_(not_(A)))


class TestNat(CheckerTest):
    def test_introduction(self):
        self.assertType(self.sets, zero, N)
        self.assertType(self.sets, succ(zero), N)
        self.assertType(self.sets, numeral(3), N)
        with self.assertRaises(TypingError):
            self.infer(self.sets, succ(true))

    def test_elimination(self):
        """test_natural.test_natural_elimination, with a genuine family."""
        C = Var("C", Arrow(A0, A0))
        n, c, f = Var("n"), Var("c"), Var("f")
        x, y = self.x, self.y
        ctx = self.sets.extend(C, SET, hyps=[(self.z, N)]).extend(n, N)
        ctx = ctx.extend(c, C(zero))
        ctx = ctx.extend(f, forall(N, abstract(implies(C(x), C(succ(x))), [x])))
        e = abstract(apply(apply(f, x), y), [x, y])
        self.assertType(ctx, natrec(C, n, c, e), C(n))
        self.assertType(ctx, natrec(C, zero, c, e), C(zero))
        self.assertType(ctx, natrec(C, succ(n), c, e), C(succ(n)))
        # wrong base case
        with self.assertRaises(TypingError):
            self.infer(ctx, natrec(C, n, apply(apply(f, zero), c), e))
        # step that does not step
        with self.assertRaises(TypingError):
            self.infer(ctx, natrec(C, n, c, abstract(y, [x, y])))

    def test_addone(self):
        """[ST] p102"""
        n, y, x = Var("n"), Var("y"), self.x
        step = abstract(succ(y), [n, y])
        addone = lam(abstract(natrec(const_family(N), x, succ(zero), step), [x]))
        self.check(self.sets, addone, implies(N, N))
        with self.assertRaises(TypingError):
            self.check(self.sets, addone, implies(N, Bool))
        # an applied λ has no inferable type (λ carries no domain); the
        # derivation layer tracks it. Under a hypothesis it is fine:
        f = Var("addone")
        ctx = self.sets.extend(f, implies(N, N))
        self.assertType(ctx, apply(f, numeral(2)), N)
        self.assertEqual(
            self.checker.evaluator.nf(apply(addone, numeral(2))), numeral(3)
        )


class TestBool(CheckerTest):
    def test_ifthenelse(self):
        C, c, d, b = self.C, Var("c"), Var("d"), Var("b")
        ctx = self.sets.extend(c, C).extend(d, C).extend(b, Bool)
        self.assertType(ctx, true, Bool)
        self.assertType(ctx, ifthenelse(b, c, d), C)
        self.assertType(ctx, ifthenelse(true, c, d), C)
        with self.assertRaises(TypingError):
            self.infer(ctx, ifthenelse(c, c, d))
        with self.assertRaises(TypingError):
            self.infer(ctx, ifthenelse(b, c, b))
        K = Var("K", Arrow(A0, A0))
        ctx = ctx.extend(K, SET, hyps=[(self.z, Bool)])
        kt, kf = Var("kt"), Var("kf")
        ctx = ctx.extend(kt, K(true)).extend(kf, K(false))
        self.assertType(ctx, boolrec(K, b, kt, kf), K(b))
        self.assertType(ctx, boolrec(K, false, kt, kf), K(false))


class TestErrors(CheckerTest):
    def test_messages(self):
        with self.assertRaises(TypingError):
            self.infer(Context(), Var("q"))
        with self.assertRaises(TypingError):
            self.infer(Context(), Const("mystery"))
        with self.assertRaises(TypingError):
            self.infer(self.sets, Var("F", Arrow(A0, A0)))  # not saturated
        with self.assertRaises(TypingError):
            self.sets.extend(self.A, SET)  # duplicate


if __name__ == "__main__":
    unittest.main()
