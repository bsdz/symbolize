"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import (A0, Abs, Arrow, Bound, Comb, Const, Cross, Sel,
                             Var, abstract)
from symbolize.terms.decl import DeclarationError, Registry, Rule
from symbolize.terms.eval import Evaluator, ReductionLimit, defeq, nf, whnf


def naturals():
    """A registry with N, zero, succ, natrec and plus, as in [BN] ch. 7."""
    reg = Registry()
    zero = Const("zero")
    succ = Const("succ", Arrow(A0, A0))
    fam = Arrow(A0, A0)
    step = Arrow(Cross((A0, A0)), A0)
    natrec = Const("natrec", Arrow(Cross((fam, A0, A0, step)), A0))
    C, n, d, e = Var("C", fam), Var("n"), Var("d"), Var("e", step)
    reg.add_rule(natrec(C, zero, d, e), d)
    reg.add_rule(natrec(C, succ(n), d, e), e(n, natrec(C, n, d, e)))
    # plus(m, n) := natrec(K, n, m, (x, y) succ(y))  for some constant family K
    K = Const("K", fam)
    m, x, y = Var("m"), Var("x"), Var("y")
    plus = Const("plus", Arrow(Cross((A0, A0)), A0))
    reg.define(plus, abstract(natrec(K, n, m, abstract(succ(y), [x, y])), [m, n]))
    return reg, zero, succ, natrec, plus


def num(k, zero, succ):
    t = zero
    for _ in range(k):
        t = succ(t)
    return t


class TestBeta(unittest.TestCase):
    def setUp(self):
        self.x, self.y, self.a, self.b = Var("x"), Var("y"), Var("a"), Var("b")
        self.f = Const("f", Arrow(A0, A0))
        self.g = Const("g", Arrow(Cross((A0, A0)), A0))

    def test_simple_beta(self):
        ident = abstract(self.x, [self.x])
        self.assertEqual(whnf(ident(self.a)), self.a)
        self.assertEqual(
            whnf(abstract(self.f(self.x), [self.x])(self.a)), self.f(self.a)
        )

    def test_beta_is_head_only(self):
        ident = abstract(self.x, [self.x])
        t = self.f(ident(self.a))
        self.assertEqual(whnf(t), t)  # f is stuck; argument untouched
        self.assertEqual(nf(t), self.f(self.a))

    def test_multi_binder(self):
        swap = abstract(self.g(self.y, self.x), [self.x, self.y])
        self.assertEqual(whnf(swap(self.a, self.b)), self.g(self.b, self.a))
        # a single argument of cross arity is projected
        p = Var("p", Cross((A0, A0)))
        self.assertEqual(whnf(swap(p)), self.g(Sel(p, 1), Sel(p, 0)))
        # a single binder of cross arity receives the combination
        q = Var("q", Cross((A0, A0)))
        first = abstract(Sel(q, 0), [q])
        self.assertEqual(whnf(first(self.a, self.b)), self.a)

    def test_curried(self):
        k = abstract(abstract(self.x, [self.y]), [self.x])
        self.assertEqual(whnf(k(self.a)(self.b)), self.a)
        self.assertEqual(nf(k(self.a)), abstract(self.a, [self.y]))

    def test_no_capture_through_beta(self):
        # ((x)(y)g(x, y))(y)  ->  (y')g(y, y')
        inner = abstract(self.g(self.x, self.y), [self.y])
        outer = abstract(inner, [self.x])
        result = nf(outer(self.y))
        self.assertEqual(result, Abs((A0,), self.g(self.y, Bound(0))))
        self.assertEqual(repr(result), "(y')g(y, y')")


class TestSelection(unittest.TestCase):
    def test_select_from_combination(self):
        a, b = Var("a"), Var("b")
        self.assertEqual(whnf(Sel(Comb((a, b)), 0)), a)
        self.assertEqual(whnf(Sel(Comb((a, b)), 1)), b)

    def test_select_from_variable_is_stuck(self):
        p = Var("p", Cross((A0, A0)))
        self.assertEqual(whnf(Sel(p, 0)), Sel(p, 0))

    def test_select_after_beta(self):
        x, y = Var("x"), Var("y")
        pair = abstract(Comb((y, x)), [x, y])
        self.assertEqual(whnf(Sel(pair(Var("a"), Var("b")), 0)), Var("b"))


class TestDelta(unittest.TestCase):
    def test_unfold_definition(self):
        reg = Registry()
        x, a = Var("x"), Var("a")
        f = Const("f", Arrow(A0, A0))
        ident = Const("id", Arrow(A0, A0))
        reg.define(ident, abstract(x, [x]))
        self.assertEqual(whnf(ident(a), reg), a)
        c, k = Const("c"), Const("k")
        reg.define(c, f(k))
        self.assertEqual(whnf(c, reg), f(k))
        # without the registry nothing unfolds
        self.assertEqual(whnf(ident(a)), ident(a))

    def test_definition_validation(self):
        reg = Registry()
        with self.assertRaises(DeclarationError):
            reg.define(Const("c"), Var("x"))  # free variable
        with self.assertRaises(DeclarationError):
            reg.define(
                Const("c", Arrow(A0, A0)), Var("x")(Var("y")) if False else Const("d")
            )
        reg.define(Const("c"), Const("d"))
        with self.assertRaises(DeclarationError):
            reg.define(Const("c"), Const("e"))  # redeclared


class TestIota(unittest.TestCase):
    def setUp(self):
        self.reg, self.zero, self.succ, self.natrec, self.plus = naturals()

    def test_rules_fire(self):
        n = lambda k: num(k, self.zero, self.succ)  # noqa: E731
        self.assertEqual(nf(self.plus(n(2), n(2)), self.reg), n(4))
        self.assertEqual(nf(self.plus(n(0), n(3)), self.reg), n(3))
        self.assertEqual(nf(self.plus(n(3), n(0)), self.reg), n(3))

    def test_stuck_on_variable(self):
        m = Var("m")
        one = self.succ(self.zero)
        # recursion is on the second argument, so plus(m, 1) computes...
        self.assertEqual(nf(self.plus(m, one), self.reg), self.succ(m))
        # ...but plus(1, m) is stuck at natrec(K, m, ...)
        stuck = whnf(self.plus(one, m), self.reg)
        self.assertEqual(stuck.fn, self.natrec)
        self.assertEqual(stuck.args[1], m)

    def test_major_argument_is_reduced_before_matching(self):
        ident = abstract(Var("x"), [Var("x")])
        one = self.succ(self.zero)
        self.assertEqual(
            nf(self.plus(one, ident(one)), self.reg), num(2, self.zero, self.succ)
        )

    def test_rule_validation(self):
        reg = Registry()
        f = Const("f", Arrow(A0, A0))
        x, y = Var("x"), Var("y")
        with self.assertRaises(DeclarationError):
            reg.add_rule(f(x), y)  # y unbound
        with self.assertRaises(DeclarationError):
            Rule(f(x), Const("g", Arrow(A0, A0)))  # arity change
        with self.assertRaises(DeclarationError):
            Rule(abstract(x, [x])(x), x)  # lhs not constant-headed
        reg.define(Const("d", Arrow(A0, A0)), abstract(x, [x]))
        with self.assertRaises(DeclarationError):
            reg.add_rule(Const("d", Arrow(A0, A0))(x), x)  # defined and ruled

    def test_major_positions(self):
        rules = self.reg.rules(self.natrec)
        self.assertEqual(rules[0].major, (1,))
        self.assertEqual(self.reg.major(self.natrec), (1,))


class TestLaziness(unittest.TestCase):
    def setUp(self):
        self.reg = Registry()
        self.f = Const("f", Arrow(A0, A0))
        self.loop = Const("loop")
        self.reg.define(self.loop, self.f(self.loop))  # loop := f(loop)
        x, y = Var("x"), Var("y")
        self.first = Const("first", Arrow(Cross((A0, A0)), A0))
        self.reg.add_rule(self.first(x, y), x)
        self.bad = Const("bad", Arrow(A0, A0))
        self.reg.add_rule(self.bad(x), self.bad(self.f(x)))

    def test_reduction_limit(self):
        # head reduction that never settles
        with self.assertRaises(ReductionLimit):
            whnf(self.bad(Var("a")), self.reg, fuel=100)
        # head settles at f(loop) but full normalisation never does
        self.assertEqual(whnf(self.loop, self.reg, fuel=100), self.f(self.loop))
        with self.assertRaises(ReductionLimit):
            nf(self.loop, self.reg, fuel=100)
        # a fixed point is simply stuck
        fix = Const("fix")
        self.reg.define(fix, fix)
        self.assertEqual(nf(fix, self.reg, fuel=100), fix)

    def test_unused_argument_is_not_evaluated(self):
        a = Var("a")
        self.assertEqual(nf(self.first(a, self.loop), self.reg, fuel=100), a)
        self.assertEqual(nf(Sel(Comb((a, self.loop)), 0), self.reg, fuel=100), a)

    def test_whnf_leaves_arguments_alone(self):
        a = Var("a")
        f = Const("f", Arrow(A0, A0))
        self.assertEqual(whnf(f(self.loop), self.reg, fuel=100), f(self.loop))
        self.assertEqual(whnf(self.first(a, self.loop), self.reg, fuel=100), a)

    def test_cache(self):
        reg, zero, succ, natrec, plus = naturals()
        ev = Evaluator(reg)
        t = plus(num(3, zero, succ), num(3, zero, succ))
        ev.whnf(t)
        steps = ev.steps
        self.assertGreater(steps, 0)
        ev.whnf(t)
        self.assertEqual(ev.steps, steps)  # cached: no reduction repeated
        ev.nf(t)
        after_nf = ev.steps
        ev.nf(t)
        # a second nf only pays for the traversal, not the reductions
        self.assertLess(ev.steps - after_nf, after_nf - steps)


class TestDefeq(unittest.TestCase):
    def setUp(self):
        self.reg, self.zero, self.succ, self.natrec, self.plus = naturals()
        self.x, self.y, self.a = Var("x"), Var("y"), Var("a")
        self.f = Const("f", Arrow(A0, A0))
        self.g = Const("g", Arrow(Cross((A0, A0)), A0))

    def test_structural_and_computational(self):
        n = lambda k: num(k, self.zero, self.succ)  # noqa: E731
        self.assertTrue(defeq(self.plus(n(1), n(2)), n(3), self.reg))
        self.assertFalse(defeq(self.plus(n(1), n(2)), n(4), self.reg))
        self.assertTrue(defeq(self.f(self.x), self.f(self.x)))
        self.assertFalse(defeq(self.f(self.x), self.f(self.y)))
        self.assertFalse(defeq(self.x, self.f))  # different arities

    def test_alpha_and_under_binder(self):
        ident = abstract(self.x, [self.x])
        self.assertTrue(
            defeq(
                abstract(self.f(self.x), [self.x]), abstract(self.f(self.y), [self.y])
            )
        )
        self.assertTrue(
            defeq(abstract(ident(self.x), [self.x]), abstract(self.y, [self.y]))
        )
        m = Var("m")
        one = self.succ(self.zero)
        lhs = abstract(self.plus(m, one), [m])
        rhs = abstract(self.succ(m), [m])
        self.assertTrue(defeq(lhs, rhs, self.reg))

    def test_eta_for_functions(self):
        self.assertTrue(defeq(abstract(self.f(self.x), [self.x]), self.f))
        self.assertTrue(defeq(self.f, abstract(self.f(self.x), [self.x])))
        self.assertTrue(
            defeq(abstract(self.g(self.x, self.y), [self.x, self.y]), self.g)
        )
        self.assertFalse(
            defeq(abstract(self.g(self.y, self.x), [self.x, self.y]), self.g)
        )

    def test_eta_for_combinations(self):
        p = Var("p", Cross((A0, A0)))
        self.assertTrue(defeq(Comb((Sel(p, 0), Sel(p, 1))), p))
        self.assertFalse(defeq(Comb((Sel(p, 1), Sel(p, 0))), p))
        self.assertTrue(
            defeq(Comb((self.a, self.f(self.a))), Comb((self.a, self.f(self.a))))
        )

    def test_nf_under_binder(self):
        ident = abstract(self.x, [self.x])
        self.assertEqual(
            nf(abstract(ident(self.x), [self.x])), abstract(self.x, [self.x])
        )
        m = Var("m")
        self.assertEqual(
            nf(abstract(self.plus(m, self.succ(self.zero)), [m]), self.reg),
            abstract(self.succ(m), [m]),
        )


if __name__ == "__main__":
    unittest.main()
