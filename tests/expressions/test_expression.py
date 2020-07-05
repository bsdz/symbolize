"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest
from copy import deepcopy

from symbolize.expressions import (
    Symbol,
    ExpressionException,
    general_bind_expression_generator,
    ExpressionCombination,
)
from symbolize.expressions import (
    APPLY_LEFT_BRACKET,
    APPLY_RIGHT_BRACKET,
    ABSTRACT_LEFT_BRACKET,
    ABSTRACT_RIGHT_BRACKET,
    SUBSTITUTE_LEFT_BRACKET,
    SUBSTITUTE_RIGHT_BRACKET,
)
from symbolize.expressions.arity import ArityArrow, ArityCross, A0

bracket_map = {
    "APL": APPLY_LEFT_BRACKET,
    "APR": APPLY_RIGHT_BRACKET,
    "ABL": ABSTRACT_LEFT_BRACKET,
    "ABR": ABSTRACT_RIGHT_BRACKET,
    "SBL": SUBSTITUTE_LEFT_BRACKET,
    "SBR": SUBSTITUTE_RIGHT_BRACKET,
}

plus = Symbol("+", arity=ArityArrow(ArityCross(A0, A0), A0))


class ExpressionTest(unittest.TestCase):
    def test_expression_simple(self):
        self.assertEqual(repr(Symbol("y")), "y")
        self.assertEqual(repr(Symbol("sin(y)")), "sin(y)")

    def test_apply(self):
        y = Symbol("y")
        sin_y = Symbol("sin(y)")
        self.assertEqual(
            repr(plus.apply(y, sin_y)), "+{APL}y, sin(y){APR}".format(**bracket_map)
        )

        x = Symbol("x")
        z = Symbol("z", ArityArrow(ArityCross(A0, A0), A0))
        self.assertEqual(repr(z.apply(x, y)), "z(x, y)")
        self.assertEqual(z.apply(x, y).arity, A0, "correct arity after apply")

        sin = Symbol("sin", arity=ArityArrow(A0, A0))
        self.assertEqual(sin.apply(x).arity, A0, "correct arity after apply")

    def test_apply_bad_arity(self):
        y = Symbol("y")
        x = Symbol("x")
        with self.assertRaises(ExpressionException) as cm:
            y.apply(x)
        self.assertIn("arity has no arrow", str(cm.exception))

        z = Symbol("z", ArityArrow(ArityCross(A0, A0), A0))
        sin = Symbol("sin", ArityArrow(A0, A0))
        with self.assertRaises(ExpressionException) as cm:
            z.apply(x, sin)
        self.assertIn("does not match child arity", str(cm.exception))

    def test_abstract(self):
        y = Symbol("y")
        sin_y = Symbol("sin(y)")
        self.assertEqual(
            repr(plus.apply(y, sin_y).abstract(y)),
            "{ABL}y{ABR}+{APL}y, sin(y){APR}".format(**bracket_map),
        )

        self.assertEqual(
            plus.apply(y, sin_y).abstract(y).arity,
            ArityArrow(A0, A0),
            "arity from abstraction",
        )

    def test_substitution(self):
        x, y, z = map(Symbol, "xyz")

        self.assertEqual(
            repr(x.substitute(y, z)), "x{SBL}y:=z{SBR}".format(**bracket_map)
        )

        # todo how does substitution affect arity in general?
        # self.assertEqual(x.substitute(y, z).arity, '', "arity from abstraction")

    def test_walk(self):
        u, v, w, x, y, z = [Symbol(i) for i in "uvwxyz"]

        u.arity = ArityArrow(ArityCross(A0, A0), A0)
        w.arity = ArityArrow(ArityCross(A0, A0, A0), A0)

        collected = []

        def func1(wr):
            return collected.append(wr)

        u(v, w(x, y, z)).abstract(x, y).walk(func1)
        self.assertGreater(len(collected), 0, "collect data")

        collected2 = []

        def func2(wr):
            collected2.append(wr)
            if type(wr.expr) is Symbol and wr.expr == x:
                raise Exception("Found")

        try:
            u(v, w(x, y, z)).walk(func2)
        except:  # noqa
            pass
        self.assertGreater(len(collected2), 0, "collect data")

        self.assertGreater(len(collected), len(collected2), "collect data")

    def test_contains(self):
        u, v, w, x, y, z = [Symbol(i) for i in "uvwxyz"]
        self.assertIn(x, x, "same expr")

        u.arity = ArityArrow(ArityCross(A0, A0), A0)
        w.arity = ArityArrow(ArityCross(A0, A0, A0), A0)
        self.assertIn(x, u(v, w(x, y, z)), "in nested expr")

    def test_contains_bind(self):
        s, t, u, v, w, x, y, z = [Symbol(i) for i in "stuvwxyz"]
        u.arity = ArityArrow(ArityCross(A0, A0), A0)
        s.arity = ArityArrow(ArityCross(ArityArrow(A0, A0), A0), A0)
        expr = s(u(v, w).abstract(x), t).abstract(y, z)
        for i in (x, y, z):
            self.assertTrue(expr.contains_bind(i), "has bind")
        for i in (s, t, u, v):
            self.assertFalse(expr.contains_bind(i), "hasn't bind")

    def test_contains_free(self):
        r, s, t, u, v, w, x, y, z = [Symbol(i) for i in "rstuvwxyz"]
        u.arity = ArityArrow(ArityCross(A0, A0), A0)
        s.arity = ArityArrow(ArityCross(ArityArrow(A0, A0), A0), A0)
        expr = s(u(v, w).abstract(x), t).abstract(y, z)
        for i in (x, y, z):
            self.assertTrue(expr.contains_bind(i), "has bind")
        for i in (r, s, t, u, v):
            self.assertFalse(expr.contains_bind(i), "hasn't bind")
        for i in (r, x, y, z):
            self.assertFalse(expr.contains_free(i), "not free")
        for i in (s, t, u, v):
            self.assertTrue(expr.contains_free(i), "is free")

    def test_replace(self):
        s, t, u, v, w, x, y, z = [Symbol(i) for i in "stuvwxyz"]
        u.arity = ArityArrow(ArityCross(A0, A0), A0)
        w.arity = ArityArrow(ArityCross(A0, A0, A0), A0)

        u1 = Symbol("u1", arity=ArityArrow(ArityCross(A0, A0), A0))
        u2 = Symbol("u2", arity=ArityArrow(ArityCross(A0, A0), A0))

        tests = [
            [x.replace(x, x), x],
            [u(v, w(x, y, z)).replace(x, s), u(v, w(s, y, z))],
            [u(v, w(x, y, z)).replace(s, t), u(v, w(x, y, z))],
            [u(v, w(x, y, z)).replace(x, s).replace(y, t), u(v, w(s, t, z))],
            [u1(x, y).replace(u1, u2), u2(x, y)],
            [u1(x, y).abstract(z).replace(x, s), u1(s, y).abstract(z)],
        ]

        for i, (e1, e2) in enumerate(tests):
            self.assertEqual(e1, e2, "check sub %s" % i)

    def test_general_bind_form(self):
        s, t, u, v, w, x, y, z = [Symbol(i) for i in "stuvwxyz"]
        u1 = Symbol("u1", arity=ArityArrow(ArityCross(A0, A0), A0))
        # u2 = Symbol("u2", arity=ArityArrow(ArityCross(A0, A0), A0))

        gbe_gen = general_bind_expression_generator()
        gbe1 = next(gbe_gen)
        gbe2 = next(gbe_gen)

        gbe1_u1 = deepcopy(gbe1)
        gbe1_u1.arity = u1.arity

        tests = [
            [u1(x, y).abstract(z).general_bind_form(), u1(x, y).abstract(gbe1)],
            [u1(x, z).abstract(z).general_bind_form(), u1(x, gbe1).abstract(gbe1)],
            [
                u1(x, y).abstract(v, w).general_bind_form(),
                u1(x, y).abstract(gbe1, gbe2),
            ],
            [
                u1(v, w).abstract(v, w).general_bind_form(),
                u1(gbe1, gbe2).abstract(gbe1, gbe2),
            ],
            [
                u1(x, y).abstract(u1).general_bind_form(),
                gbe1_u1(x, y).abstract(gbe1_u1),
            ],
        ]

        for i, (e1, e2) in enumerate(tests):
            self.assertEqual(e1, e2, "check general bind form %s" % i)

    def test_beta_reduction(self):
        s, t, u, v, w, x, y, z = [Symbol(i) for i in "stuvwxyz"]
        u1 = Symbol("u1", arity=ArityArrow(ArityCross(A0, A0), A0))
        # u2 = Symbol("u2", arity=ArityArrow(ArityCross(A0, A0), A0))

        tests = [
            [u1(x, y).abstract(x).apply(z).beta_reduction(), u1(z, y)],
            [u1(x, y).abstract(x, y).apply(z, z).beta_reduction(), u1(z, z)],
            [u1(x, y).abstract(x, y).apply(v, w).beta_reduction(), u1(v, w)],
            [u1(x, y).abstract(x, y).beta_reduction(), u1(x, y).abstract(x, y)],
        ]

        for i, (e1, e2) in enumerate(tests):
            self.assertEqual(e1, e2, "check beta reduction %s" % i)


class ExpressionCombinationTest(unittest.TestCase):
    def test_combination(self):
        x, y, z = [Symbol(i) for i in "xyz"]
        expr = ExpressionCombination(x, y, z)
        self.assertEqual(repr(expr), "x, y, z")
        self.assertEqual(expr.arity, ArityCross(A0, A0, A0), "arity from combination")

    def test_selection(self):
        x, y, z = [Symbol(i) for i in "xyz"]
        expr = ExpressionCombination(x, y, z)
        self.assertEqual(expr[1], y)
        self.assertEqual(expr[1].arity, A0, "arity from selection")


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
