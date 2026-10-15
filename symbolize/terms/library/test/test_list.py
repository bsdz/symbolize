"""The List former: formation, constructors, and primitive recursion.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, Abs, Var
from symbolize.terms.binding import abstract
from symbolize.terms.check import TypingError
from symbolize.terms.decl import SET
from symbolize.terms.derive import Engine, hyp, judge, set_var
from symbolize.terms.library import (
    List,
    N,
    cons,
    listing,
    listrec,
    nil,
    numeral,
    standard,
    succ,
    zero,
)


class ListTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard())
        self.A = set_var("A", engine=self.engine)
        self.N = judge(N, SET, engine=self.engine)
        self.a = hyp("a", self.A)
        self.ctx = self.a.ctx

    def nat(self, term):
        return judge(term, N, engine=self.engine)

    def nf(self, term):
        return self.engine.evaluator.nf(term)


class TestFormation(ListTest):
    def test_list_of_a_set_is_a_set(self):
        self.engine.checker.is_set(self.A.ctx, List(self.A.term))

    def test_list_of_a_non_set_is_refused(self):
        with self.assertRaises(TypingError):
            self.engine.checker.is_set(self.ctx, List(self.a.term))


class TestConstructors(ListTest):
    def test_nil_needs_an_expected_type(self):
        """``nil``'s signature is ``() -> List(?A)``, so the element set can
        only come from the expected type."""
        self.assertEqual(
            judge(nil, List(self.A.term), self.ctx, engine=self.engine).type,
            List(self.A.term),
        )
        with self.assertRaises(TypingError) as raised:
            self.engine.checker.infer(self.ctx, nil)
        self.assertIn("expected type is needed", str(raised.exception))

    def test_cons(self):
        one = judge(
            cons(self.a.term, nil),
            List(self.A.term),
            self.ctx,
            engine=self.engine,
        )
        self.assertEqual(one.type, List(self.A.term))
        two = cons(self.a.term, one.term)
        self.engine.checker.check(self.ctx, two, List(self.A.term))

    def test_cons_rejects_a_mismatched_element(self):
        with self.assertRaises(TypingError):
            self.engine.checker.check(
                self.ctx, cons(zero, nil), List(self.A.term)
            )

    def test_listing_builds_a_literal(self):
        self.assertEqual(listing(), nil)
        self.assertEqual(listing(zero), cons(zero, nil))
        self.assertEqual(
            listing(zero, numeral(1)), cons(zero, cons(numeral(1), nil))
        )
        self.engine.checker.check(
            self.ctx, listing(*[self.a.term] * 3), List(self.A.term)
        )


class TestRecursion(ListTest):
    """``listrec`` at a concrete element set.

    A polymorphic ``length`` would need to take its element set explicitly
    (see the module docstring of ``library/list.py``), so these build the
    function at ``N`` directly.
    """

    def setUp(self):
        super().setUp()
        self.x, self.xs, self.y = Var("x"), Var("xs"), Var("y")
        const_n = Abs((A0,), N, hints=("_",))
        self.length = lambda l: listrec(
            const_n, l, zero, abstract(succ(self.y), [self.x, self.xs, self.y])
        )
        const_l = Abs((A0,), List(N), hints=("_",))
        self.append = lambda l, r: listrec(
            const_l,
            l,
            r,
            abstract(cons(self.x, self.y), [self.x, self.xs, self.y]),
        )

    def test_nil_rule(self):
        self.assertEqual(self.nf(self.length(nil)), zero)

    def test_cons_rule(self):
        got = self.nf(self.length(listing(*map(numeral, (7, 8, 9)))))
        self.assertEqual(got, numeral(3))

    def test_length_is_typed(self):
        l = judge(listing(zero, numeral(1)), List(N), engine=self.engine)
        self.assertEqual(
            judge(self.length(l.term), N, engine=self.engine).type, N
        )

    def test_append(self):
        got = self.nf(
            self.append(listing(numeral(1), numeral(2)), listing(numeral(3)))
        )
        self.assertEqual(got, listing(numeral(1), numeral(2), numeral(3)))

    def test_append_with_nil_is_the_identity(self):
        xs = listing(numeral(4), numeral(5))
        self.assertEqual(self.nf(self.append(nil, xs)), xs)
        self.assertEqual(self.nf(self.append(xs, nil)), xs)

    def test_recursion_on_a_variable_is_stuck(self):
        """Nothing evaluates on construction, and a variable list has no
        head to select on, so the recursion suspends rather than looping."""
        l = hyp("l", judge(List(N), SET, engine=self.engine))
        stuck = self.length(l.term)
        self.assertEqual(self.nf(stuck), stuck)


class TestRendering(ListTest):
    def test_styles(self):
        two = listing(zero, numeral(1))
        self.assertEqual(two.repr_typestring(), "cons(0, cons(succ(0), nil))")
        self.assertEqual(two.repr_unicode(), "0 ∷ (succ(0) ∷ [])")
        self.assertEqual(
            List(N).repr_latex(), r"\mathrm{List}(\mathbb{N})"
        )
        self.assertEqual(nil.repr_unicode(), "[]")


if __name__ == "__main__":
    unittest.main()
