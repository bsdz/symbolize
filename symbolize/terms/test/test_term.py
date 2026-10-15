"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import (A0, Abs, App, ArityError, Arrow, Bound, Comb,
                             Const, Cross, Sel, TermError, Var, arrow, cross,
                             is_closed)


class TestArity(unittest.TestCase):
    def test_equality_and_hash(self):
        self.assertEqual(Arrow(A0, A0), Arrow(A0, A0))
        self.assertEqual(hash(Arrow(A0, A0)), hash(Arrow(A0, A0)))
        self.assertNotEqual(Arrow(A0, A0), A0)
        self.assertEqual(Cross((A0, A0)), Cross((A0, A0)))
        self.assertNotEqual(Cross((A0, A0)), Cross((A0, A0, A0)))

    def test_cross_helper_collapses_singleton(self):
        self.assertIs(cross(A0), A0)
        self.assertEqual(cross(A0, A0), Cross((A0, A0)))
        with self.assertRaises(ValueError):
            Cross((A0,))
        with self.assertRaises(ValueError):
            cross()

    def test_arrow_helper_nests_right(self):
        self.assertEqual(arrow(A0, A0, A0), Arrow(A0, Arrow(A0, A0)))
        self.assertIs(arrow(A0), A0)

    def test_repr(self):
        self.assertEqual(repr(A0), "0")
        self.assertEqual(repr(Arrow(A0, A0)), "0 ⟶ 0")
        self.assertEqual(
            repr(Arrow(Cross((A0, Arrow(A0, A0))), A0)), "(0 ⊗ (0 ⟶ 0)) ⟶ 0"
        )


class TestTermConstruction(unittest.TestCase):
    def setUp(self):
        self.x = Var("x")
        self.y = Var("y")
        self.f = Const("f", Arrow(A0, A0))
        self.g = Const("g", Arrow(Cross((A0, A0)), A0))
        self.h = Const("h", Arrow(Arrow(A0, A0), A0))

    def test_leaves(self):
        self.assertEqual(self.x.arity, A0)
        self.assertEqual(Var("F", Arrow(A0, A0)).arity, Arrow(A0, A0))
        self.assertEqual(Const("c").arity, A0)

    def test_application_arity(self):
        self.assertEqual(self.f(self.x).arity, A0)
        self.assertEqual(self.g(self.x, self.y).arity, A0)
        self.assertEqual(self.h(Abs((A0,), Bound(0))).arity, A0)
        curried = Const("k", arrow(A0, A0, A0))
        self.assertEqual(curried(self.x).arity, Arrow(A0, A0))
        self.assertEqual(curried(self.x)(self.y).arity, A0)

    def test_application_rejects_bad_arity(self):
        with self.assertRaises(ArityError):
            self.x(self.y)  # 0 is not an arrow
        with self.assertRaises(ArityError):
            self.f(self.x, self.y)  # too many arguments
        with self.assertRaises(ArityError):
            self.g(self.x)  # too few
        with self.assertRaises(ArityError):
            self.h(self.x)  # expected 0 -> 0, got 0
        with self.assertRaises(ArityError):
            App(self.f, ())

    def test_combination_and_selection(self):
        c = Comb((self.x, self.f))
        self.assertEqual(c.arity, Cross((A0, Arrow(A0, A0))))
        self.assertEqual(Sel(c, 0).arity, A0)
        self.assertEqual(Sel(c, 1).arity, Arrow(A0, A0))
        with self.assertRaises(ArityError):
            Sel(c, 2)
        with self.assertRaises(ArityError):
            Sel(self.x, 0)
        with self.assertRaises(ArityError):
            Comb((self.x,))

    def test_combination_argument_is_spread(self):
        applied = self.g(Comb((self.x, self.y)))
        self.assertEqual(applied.arity, A0)
        self.assertEqual(applied, self.g(self.x, self.y))

    def test_abstraction_arity(self):
        a = Abs((A0,), self.f(Bound(0)))
        self.assertEqual(a.arity, Arrow(A0, A0))
        b = Abs((A0, A0), self.g(Bound(0), Bound(1)))
        self.assertEqual(b.arity, Arrow(Cross((A0, A0)), A0))
        c = Abs((Arrow(A0, A0),), Bound(0, Arrow(A0, A0))(self.x))
        self.assertEqual(c.arity, Arrow(Arrow(A0, A0), A0))

    def test_abstraction_checks_bound_arity(self):
        with self.assertRaises(ArityError):
            Abs((Arrow(A0, A0),), self.f(Bound(0)))
        with self.assertRaises(ArityError):
            Abs((), self.x)
        with self.assertRaises(TermError):
            Abs((A0,), self.x, hints=("a", "b"))

    def test_nested_abstraction_indices(self):
        # (x)(y)g(x, y): inside the inner binder, x is index 1
        inner = Abs((A0,), self.g(Bound(1), Bound(0)), hints=("y",))
        outer = Abs((A0,), inner, hints=("x",))
        self.assertEqual(outer.arity, Arrow(A0, Arrow(A0, A0)))
        self.assertTrue(is_closed(outer))
        self.assertFalse(is_closed(inner))

    def test_immutable_and_hashable(self):
        t = self.g(self.x, self.y)
        with self.assertRaises(Exception):
            t.args = ()
        self.assertEqual(len({t, self.g(self.x, self.y)}), 1)


class TestTermEquality(unittest.TestCase):
    def test_structural_equality(self):
        f = Const("f", Arrow(A0, A0))
        self.assertEqual(f(Var("x")), f(Var("x")))
        self.assertNotEqual(f(Var("x")), f(Var("y")))
        self.assertNotEqual(Var("x"), Const("x"))
        self.assertNotEqual(Var("x"), Var("x", Arrow(A0, A0)))

    def test_alpha_equivalence_is_structural(self):
        f = Const("f", Arrow(A0, A0))
        a = Abs((A0,), f(Bound(0)), hints=("x",))
        b = Abs((A0,), f(Bound(0)), hints=("y",))
        self.assertEqual(a, b)
        self.assertEqual(hash(a), hash(b))


class TestRepr(unittest.TestCase):
    def test_repr(self):
        x, y = Var("x"), Var("y")
        f = Const("f", Arrow(A0, A0))
        g = Const("g", Arrow(Cross((A0, A0)), A0))
        self.assertEqual(repr(f(x)), "f(x)")
        self.assertEqual(repr(g(x, y)), "g(x, y)")
        self.assertEqual(repr(Comb((x, y))), "x, y")
        self.assertEqual(repr(Sel(Comb((x, y)), 1)), "(x, y).1")
        self.assertEqual(repr(Abs((A0,), f(Bound(0)), hints=("x",))), "(x)f(x)")
        self.assertEqual(
            repr(Abs((A0, A0), g(Bound(0), Bound(1)), hints=("a", "b"))),
            "(a, b)g(a, b)",
        )
        # nested binder: inner refers to outer by index 1
        inner = Abs((A0,), g(Bound(1), Bound(0)), hints=("y",))
        self.assertEqual(repr(Abs((A0,), inner, hints=("x",))), "(x)((y)g(x, y))")
        # hint clashing with an enclosing binder is primed
        clash = Abs(
            (A0,), Abs((A0,), g(Bound(1), Bound(0)), hints=("x",)), hints=("x",)
        )
        self.assertEqual(repr(clash), "(x)((x')g(x, x'))")


if __name__ == "__main__":
    unittest.main()
