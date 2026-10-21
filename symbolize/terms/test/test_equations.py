"""Balanced manipulation of equations, as sympy's ``Eq`` is used.

Each step on a proof ``h : a = b`` gives a proof of the new equation, built
from the derived rules of ``library/identity.py``, so every result here is
re-checked independently and depends on no axiom it did not cite.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms.decl import SET
from symbolize.terms.derive import (
    DerivationError,
    Engine,
    assume,
    cite,
    cong_in,
    judge,
    literal,
    symbols,
)
from symbolize.terms.library import REAL, R, standard
from symbolize.terms.term import Var


class EquationTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard(reals=True))
        self.R = judge(R, SET, engine=self.engine)
        self.x, self.y, self.z, self.k = symbols("x y z k", self.R)
        self.h = assume((2 * self.x).eq(self.y + 1))

    def holds(self, j, text):
        """``j`` states ``text`` and re-checks from scratch."""
        self.assertEqual(j.repr_unicode().split(" : ", 1)[1], text)
        self.engine.checker.check(j.ctx, j.term, j.type)


class TestBalanced(EquationTest):
    def test_the_hypothesis(self):
        self.assertEqual(self.h.repr_unicode(), "h : 2 ⋅ x = y + 1")
        self.assertTrue(self.h.is_equation)
        self.assertFalse(self.h.lhs.is_equation)

    def test_an_operand_on_either_side(self):
        h = self.h
        cases = [
            (h + 1, "2 ⋅ x + 1 = y + 1 + 1"),
            (1 + h, "1 + 2 ⋅ x = 1 + (y + 1)"),
            (h - self.z, "2 ⋅ x - z = y + 1 - z"),
            (3 * h, "3 ⋅ (2 ⋅ x) = 3 ⋅ (y + 1)"),
            (h * self.k, "2 ⋅ x ⋅ k = (y + 1) ⋅ k"),
            (h**2, "(2 ⋅ x)² = (y + 1)²"),
            (-h, "-(2 ⋅ x) = -(y + 1)"),
        ]
        for built, text in cases:
            with self.subTest(text):
                self.holds(built, text)

    def test_two_equations_side_by_side(self):
        g = assume(self.z.eq(self.k), "g")
        self.holds(self.h + g, "2 ⋅ x + z = y + 1 + k")
        self.holds(self.h * g, "2 ⋅ x ⋅ z = (y + 1) ⋅ k")
        self.assertLessEqual({"g", "h"}, set((self.h + g).ctx.names()))

    def test_no_axioms_are_added(self):
        self.assertEqual((3 * (self.h + 1) ** 2).axioms, ())

    def test_the_proof_reads_as_the_step(self):
        self.assertEqual(
            (self.h - 1).repr_unicode(),
            "cong((t)t - 1, h) : 2 ⋅ x - 1 = y + 1 - 1",
        )

    def test_a_statement_is_not_manipulated(self):
        """Only a proof can be manipulated: ``eqn + 1`` would make a
        statement look like a step that had been justified."""
        eqn = self.x.eq(self.y)
        with self.assertRaises(DerivationError) as raised:
            eqn + 1
        self.assertIn("not a proof", str(raised.exception))


class TestApply(EquationTest):
    def test_a_python_function(self):
        self.holds(
            self.h.apply(lambda t: (t + self.z) ** 2),
            "(2 ⋅ x + z)² = (y + 1 + z)²",
        )

    def test_the_parameter_names_the_hole(self):
        r = self.h.apply(lambda u: u + 1)
        self.assertTrue(r.repr_unicode().startswith("cong((u)u + 1, h)"))

    def test_a_symbol_named_like_the_hole_is_not_captured(self):
        t = symbols("t", self.R)
        r = self.h.apply(lambda t_: t_ + t)
        self.holds(r, "2 ⋅ x + t = y + 1 + t")
        r = cong_in(lambda t: t + symbols("t", self.R), self.h)
        self.holds(r, "2 ⋅ x + t = y + 1 + t")

    def test_a_function_judgement(self):
        f = (self.R >> self.R).hyp("f")
        self.holds(self.h.apply(f), "f(2 ⋅ x) = f(y + 1)")

    def test_an_abstraction(self):
        t = Var("t")
        context = REAL.mul(t, t).abstract(t)
        self.holds(self.h.apply(context), "2 ⋅ x ⋅ (2 ⋅ x) = (y + 1) ⋅ (y + 1)")

    def test_a_constant_function(self):
        self.holds(self.h.apply(lambda t: 0), "0 = 0")

    def test_apply_on_a_function_still_applies_it(self):
        f = (self.R >> self.R).hyp("f")
        self.assertEqual(f.apply(self.x).repr_unicode(), "f(x) : ℝ")

    def test_a_context_must_give_an_element(self):
        with self.assertRaises(DerivationError):
            self.h.apply(lambda t: t.eq(t))
        with self.assertRaises(DerivationError):
            self.h.apply("t + 1")


class TestSides(EquationTest):
    def test_lhs_and_rhs(self):
        self.assertEqual(self.h.lhs.repr_unicode(), "2 ⋅ x : ℝ")
        self.assertEqual(self.h.rhs.repr_unicode(), "y + 1 : ℝ")

    def test_a_side_keeps_only_its_hypotheses(self):
        self.assertEqual(self.h.rhs.repr_context(), "[y : ℝ]")

    def test_sides_of_a_statement(self):
        eqn = self.x.eq(self.y * 2)
        self.assertEqual(eqn.rhs.repr_unicode(), "y ⋅ 2 : ℝ")

    def test_not_an_equation(self):
        with self.assertRaises(DerivationError):
            self.x.lhs

    def test_flip(self):
        self.holds(self.h.flip(), "y + 1 = 2 ⋅ x")
        self.assertEqual(
            self.h.flip().repr_unicode().split(" : ")[0], "symm(h)"
        )
        statement = self.x.eq(self.y).flip()
        self.assertTrue(statement.is_set)
        self.assertEqual(statement.repr_unicode(), "y = x")


class TestSubs(EquationTest):
    def setUp(self):
        super().setUp()
        self.d = assume(self.y.eq(self.z * self.z), "d")

    def test_both_sides(self):
        self.holds(
            (self.h + self.y).subs(self.d), "2 ⋅ x + z ⋅ z = z ⋅ z + 1 + z ⋅ z"
        )

    def test_one_side(self):
        g = self.h + self.y
        self.holds(g.subs(self.d, at="rhs"), "2 ⋅ x + y = z ⋅ z + 1 + z ⋅ z")
        self.holds(g.subs(self.d, at="lhs"), "2 ⋅ x + z ⋅ z = y + 1 + y")

    def test_the_other_way(self):
        self.holds(self.h.subs(self.d).subs(self.d.flip()), "2 ⋅ x = y + 1")

    def test_occurrence_indices_still_work(self):
        g = self.h + self.y
        self.holds(g.subs(self.d, at=[1]), "2 ⋅ x + y = z ⋅ z + 1 + y")

    def test_absent_from_the_side(self):
        with self.assertRaises(DerivationError) as raised:
            self.h.subs(self.d, at="lhs")
        self.assertIn("left side", str(raised.exception))

    def test_bad_side(self):
        with self.assertRaises(DerivationError):
            self.h.subs(self.d, at="middle")

    def test_a_statement_cannot_be_substituted_into(self):
        with self.assertRaises(DerivationError):
            self.x.eq(self.y).subs(self.d)


class TestOneSided(EquationTest):
    def test_rhs_by(self):
        comm = cite(REAL.add_comm, self.y, literal(1, self.R))
        self.holds(self.h.rhs_by(comm), "2 ⋅ x = 1 + y")

    def test_either_orientation(self):
        comm = cite(REAL.add_comm, literal(1, self.R), self.y)
        self.holds(self.h.rhs_by(comm), "2 ⋅ x = 1 + y")

    def test_lhs_by(self):
        comm = cite(REAL.mul_comm, literal(2, self.R), self.x)
        self.holds(self.h.lhs_by(comm), "x ⋅ 2 = y + 1")
        self.holds(self.h.lhs_by(comm.flip()), "x ⋅ 2 = y + 1")

    def test_unrelated(self):
        comm = cite(REAL.add_comm, self.x, self.y)
        with self.assertRaises(DerivationError) as raised:
            self.h.rhs_by(comm)
        self.assertIn("right side", str(raised.exception))


class TestAssume(EquationTest):
    def test_names_are_fresh(self):
        eqn = self.x.eq(self.y)
        self.assertEqual(assume(eqn).term.name, "h")
        self.assertEqual(eqn.assume("e").term.name, "e")
        # a statement that already depends on h gets h'
        self.assertEqual(assume(self.h.eq(self.h)).term.name, "h'")

    def test_a_derivation_discharged_is_a_theorem(self):
        """``2x = y + 1 ⇒ 2x - 1 = y + 1 - 1``: the step, as a theorem."""
        theorem = (self.h - 1).discharge(self.h)
        self.holds(theorem, "(2 ⋅ x = y + 1) ⟹ (2 ⋅ x - 1 = y + 1 - 1)")
        self.assertNotIn("h", theorem.ctx.names())


class TestWorkedExample(EquationTest):
    """A ring-only step in the shape of the Asian-options moment derivation:
    from ``u - τ = m`` recover ``u = m + τ``, then scale by ``κ``. Each
    one-sided simplification is a chain of cited ring laws."""

    def test_rearranging(self):
        u, tau, m, kappa = symbols("u tau m kappa", self.R)
        h = assume((u - tau).eq(m))
        step = h + tau  # u - τ + τ = m + τ
        self.holds(step, "u - tau + tau = m + tau")

        # u - τ + τ = u, since subtraction is adding the negation
        cancel = (
            cite(REAL.add_assoc, u, -tau, tau)
            .rhs_by(
                cong_in(
                    lambda s: u + s,
                    cite(REAL.add_comm, -tau, tau).trans(
                        cite(REAL.add_neg_cancel, tau)
                    ),
                )
            )
            .rhs_by(cite(REAL.add_zero, u))
        )
        self.holds(cancel, "u + -tau + tau = u")

        solved = step.lhs_by(cancel)
        self.holds(solved, "u = m + tau")
        scaled = solved * kappa
        self.holds(scaled, "u ⋅ kappa = (m + tau) ⋅ kappa")

        theorem = scaled.discharge(h)
        self.holds(theorem, "(u - tau = m) ⟹ (u ⋅ kappa = (m + tau) ⋅ kappa)")
        self.assertEqual(
            set(theorem.axioms),
            {
                REAL.add_assoc,
                REAL.add_comm,
                REAL.add_neg_cancel,
                REAL.add_zero,
            },
        )


if __name__ == "__main__":
    unittest.main()
