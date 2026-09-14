"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import (
    A0,
    Abs,
    ArityError,
    Arrow,
    Bound,
    Comb,
    Const,
    Cross,
    Sel,
    TermError,
    Var,
    abstract,
    contains_free,
    free_vars,
    instantiate,
    is_closed,
    open_abs,
    subst,
    subst_many,
)


class TestFreeVars(unittest.TestCase):
    def setUp(self):
        self.x, self.y, self.z = Var("x"), Var("y"), Var("z")
        self.f = Const("f", Arrow(A0, A0))
        self.g = Const("g", Arrow(Cross((A0, A0)), A0))

    def test_free_vars(self):
        t = self.g(self.f(self.x), self.y)
        self.assertEqual(free_vars(t), {self.x, self.y})
        self.assertEqual(free_vars(Comb((t, self.z))), {self.x, self.y, self.z})
        self.assertEqual(free_vars(self.f), frozenset())
        self.assertEqual(free_vars(Sel(Comb((self.x, self.y)), 0)), {self.x, self.y})

    def test_bound_variables_are_not_free(self):
        t = abstract(self.g(self.x, self.y), [self.x])
        self.assertEqual(free_vars(t), {self.y})
        self.assertTrue(contains_free(t, self.y))
        self.assertFalse(contains_free(t, self.x))

    def test_free_and_bound_occurrences_of_same_name(self):
        # u(x, (x)w(x, y)): the outer x is free, the inner is bound.
        # This is the case the old core got wrong.
        u = Const("u", Arrow(Cross((A0, Arrow(A0, A0))), A0))
        w = self.g
        inner = abstract(w(self.x, self.y), [self.x])
        t = u(self.x, inner)
        self.assertTrue(contains_free(t, self.x))
        self.assertEqual(free_vars(t), {self.x, self.y})


class TestAbstractInstantiate(unittest.TestCase):
    def setUp(self):
        self.x, self.y, self.z = Var("x"), Var("y"), Var("z")
        self.f = Const("f", Arrow(A0, A0))
        self.g = Const("g", Arrow(Cross((A0, A0)), A0))

    def test_abstract_single(self):
        a = abstract(self.g(self.x, self.y), [self.x])
        self.assertEqual(a, Abs((A0,), self.g(Bound(0), self.y)))
        self.assertEqual(a.hints, ("x",))
        self.assertEqual(a.arity, Arrow(A0, A0))
        self.assertTrue(is_closed(a))

    def test_abstract_multiple(self):
        a = abstract(self.g(self.x, self.y), [self.y, self.x])
        self.assertEqual(a, Abs((A0, A0), self.g(Bound(1), Bound(0))))
        self.assertEqual(a.hints, ("y", "x"))
        self.assertEqual(repr(a), "(y, x)g(x, y)")

    def test_abstract_higher_arity_variable(self):
        F = Var("F", Arrow(A0, A0))
        a = abstract(F(self.x), [F])
        self.assertEqual(a.arity, Arrow(Arrow(A0, A0), A0))
        self.assertEqual(a, Abs((Arrow(A0, A0),), Bound(0, Arrow(A0, A0))(self.x)))

    def test_abstract_nested_shifts_correctly(self):
        # abstracting x out of (y)g(x, y) must skip the inner binder
        inner = abstract(self.g(self.x, self.y), [self.y])
        outer = abstract(inner, [self.x])
        self.assertEqual(
            outer,
            Abs((A0,), Abs((A0,), self.g(Bound(1), Bound(0)))),
        )
        self.assertEqual(repr(outer), "(x)((y)g(x, y))")

    def test_abstract_rejects_bad_input(self):
        with self.assertRaises(TermError):
            abstract(self.x, [])
        with self.assertRaises(TermError):
            abstract(self.x, [self.x, self.x])

    def test_instantiate_round_trip(self):
        t = self.g(self.f(self.x), self.y)
        a = abstract(t, [self.x])
        self.assertEqual(instantiate(a, [self.x]), t)
        self.assertEqual(instantiate(a, [self.z]), self.g(self.f(self.z), self.y))

    def test_instantiate_multiple_and_with_open_terms(self):
        a = abstract(self.g(self.x, self.y), [self.x, self.y])
        self.assertEqual(instantiate(a, [self.y, self.x]), self.g(self.y, self.x))
        self.assertEqual(
            instantiate(a, [self.f(self.z), self.z]),
            self.g(self.f(self.z), self.z),
        )

    def test_instantiate_no_capture(self):
        # ((x)(y)g(x, y)) applied to y must not capture the inner y
        inner = abstract(self.g(self.x, self.y), [self.y])
        outer = abstract(inner, [self.x])
        opened = instantiate(outer, [self.y])
        self.assertEqual(opened, Abs((A0,), self.g(self.y, Bound(0))))
        self.assertEqual(repr(opened), "(y')g(y, y')")

    def test_instantiate_nested_binder_body(self):
        # opening the outer binder shifts references to it inside the inner
        inner = Abs((A0,), self.g(Bound(1), Bound(0)))
        outer = Abs((A0,), inner)
        self.assertEqual(
            instantiate(outer, [self.z]), Abs((A0,), self.g(self.z, Bound(0)))
        )

    def test_instantiate_checks_arity(self):
        a = abstract(self.g(self.x, self.y), [self.x])
        with self.assertRaises(ArityError):
            instantiate(a, [self.x, self.y])
        with self.assertRaises(ArityError):
            instantiate(a, [self.f])

    def test_open_abs_gives_fresh_variables(self):
        a = abstract(self.g(self.x, self.y), [self.x])
        (v,), body = open_abs(a)
        self.assertEqual(v, self.x)
        self.assertEqual(body, self.g(self.x, self.y))
        # hint clashes with a free variable: freshened
        (v2,), body2 = open_abs(a, avoid=["x"])
        self.assertEqual(v2.name, "x'")
        self.assertEqual(body2, self.g(v2, self.y))
        b = abstract(self.g(self.x, self.y), [self.x], hints=["y"])
        (v3,), body3 = open_abs(b)
        self.assertEqual(v3.name, "y'")


class TestSubst(unittest.TestCase):
    def setUp(self):
        self.x, self.y, self.z = Var("x"), Var("y"), Var("z")
        self.f = Const("f", Arrow(A0, A0))
        self.g = Const("g", Arrow(Cross((A0, A0)), A0))

    def test_subst_free(self):
        t = self.g(self.f(self.x), self.x)
        self.assertEqual(subst(t, self.x, self.y), self.g(self.f(self.y), self.y))
        self.assertEqual(subst(t, self.z, self.y), t)

    def test_subst_only_free_occurrences(self):
        u = Const("u", Arrow(Cross((A0, Arrow(A0, A0))), A0))
        inner = abstract(self.g(self.x, self.y), [self.x])
        t = u(self.x, inner)
        self.assertEqual(subst(t, self.x, self.y), u(self.y, inner))

    def test_subst_cannot_capture(self):
        # (y)g(x, y) [x := y]  must be (y')g(y, y')
        inner = abstract(self.g(self.x, self.y), [self.y])
        result = subst(inner, self.x, self.y)
        self.assertEqual(result, Abs((A0,), self.g(self.y, Bound(0))))
        self.assertEqual(repr(result), "(y')g(y, y')")
        # and opening it confirms the two y's are different variables
        (v,), body = open_abs(result)
        self.assertNotEqual(v, self.y)
        self.assertEqual(body, self.g(self.y, v))

    def test_subst_many_is_simultaneous(self):
        t = self.g(self.x, self.y)
        self.assertEqual(
            subst_many(t, {self.x: self.y, self.y: self.x}), self.g(self.y, self.x)
        )

    def test_subst_checks_arity(self):
        with self.assertRaises(ArityError):
            subst(self.f(self.x), self.x, self.f)

    def test_subst_family_variable(self):
        C = Var("C", Arrow(A0, A0))
        t = C(self.x)
        self.assertEqual(subst(t, C, self.f), self.f(self.x))
        body = abstract(self.g(self.x, self.x), [self.x])
        self.assertEqual(subst(t, C, body), body(self.x))


if __name__ == "__main__":
    unittest.main()
