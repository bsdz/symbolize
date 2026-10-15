"""Commutative rings: what is declared, what is believed, what computes.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import ArityError, Const
from symbolize.terms.decl import SET, DeclarationError
from symbolize.terms.derive import (
    DerivationError,
    Engine,
    cite,
    judge,
    literal,
    symbols,
)
from symbolize.terms.library import (
    REAL,
    N,
    R,
    commutative_ring,
    natrec,
    numeral,
    real,
    standard,
)


class RingTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard(reals=True))
        self.R = judge(R, SET, engine=self.engine)
        self.x, self.y, self.z = symbols("x y z", self.R)

    def nf(self, j):
        return self.engine.nf(j.term)


class TestDeclaration(RingTest):
    def test_reals_are_opt_in(self):
        """The ring laws are axioms, so a standard registry stays free of
        them unless asked."""
        self.assertEqual(standard().axioms(), ())
        self.assertNotIn(R, standard())

    def test_the_laws_are_the_only_axioms(self):
        self.assertEqual(set(self.engine.registry.axioms()), set(REAL.laws))
        self.assertEqual(len(REAL.laws), 8)

    def test_operations_are_primitive_not_axioms(self):
        registry = self.engine.registry
        for op in (REAL.zero, REAL.one, REAL.add, REAL.mul, REAL.neg):
            with self.subTest(op.name):
                self.assertIsNotNone(registry.signature(op))
                self.assertIsNone(registry.definition(op))
                self.assertFalse(registry.is_axiom(op))

    def test_provenance_states_the_law(self):
        record = self.engine.registry.provenance(REAL.mul_add)
        self.assertEqual(record.statement, "a ⋅ (b + c) = a ⋅ b + a ⋅ c")
        self.assertIn("Mathlib: mul_add", record.note)
        self.assertTrue(record.digest)

    def test_each_law_states_what_it_says(self):
        statements = {
            "add_assoc": "a + b + c = a + (b + c)",
            "add_comm": "a + b = b + a",
            "add_zero": "a + 0 = a",
            "add_neg_cancel": "a + -a = 0",
            "mul_assoc": "a ⋅ b ⋅ c = a ⋅ (b ⋅ c)",
            "mul_comm": "a ⋅ b = b ⋅ a",
            "mul_one": "a ⋅ 1 = a",
            "mul_add": "a ⋅ (b + c) = a ⋅ b + a ⋅ c",
        }
        for law in REAL.laws:
            name = law.name.split(".")[1]
            with self.subTest(name):
                record = self.engine.registry.provenance(law)
                self.assertEqual(record.statement, statements[name])

    def test_declaring_twice_is_refused(self):
        with self.assertRaises(DeclarationError):
            real.declare(self.engine.registry)

    def test_one_ring_in_several_registries(self):
        a, b = standard(), standard()
        REAL.declare(a)
        REAL.declare(b)
        self.assertEqual(a.axioms(), b.axioms())


class TestAnotherCarrier(unittest.TestCase):
    def test_a_ring_on_a_fresh_carrier(self):
        Z = Const("Z")
        ring = commutative_ring(Z)
        registry = standard()
        ring.declare(registry)
        engine = Engine(registry)
        self.assertEqual(ring.add.name, "Z.add")
        a, b = symbols("a b", judge(Z, SET, engine=engine))
        law = cite(ring.add_comm, a, b)
        self.assertEqual(law.repr_unicode(), "Z.add_comm(a, b) : a + b = b + a")

    def test_the_prefix_can_be_chosen(self):
        ring = commutative_ring(Const("Q"), prefix="Rat")
        self.assertEqual(ring.mul_comm.name, "Rat.mul_comm")


class TestDefinitions(RingTest):
    """Subtraction, powers and literals are definitions: they cost no trust
    and unfold, recursing as Lean's ``Monoid.npow`` and ``Nat.cast``."""

    def test_subtraction_is_adding_the_negation(self):
        self.assertTrue((self.x - self.y).defeq(self.x + -self.y))

    def test_power_unfolds_by_recursion_on_the_exponent(self):
        self.assertTrue((self.x**0).defeq(literal(1, self.R)))
        self.assertTrue((self.x**2).defeq(1 * self.x * self.x))
        self.assertEqual(self.nf(self.x**2).repr_unicode(), "1 ⋅ x ⋅ x")

    def test_literals_unfold_to_sums_of_one(self):
        self.assertEqual(
            self.nf(literal(3, self.R)).repr_unicode(), "0 + 1 + 1 + 1"
        )

    def test_small_literals_are_the_constants(self):
        self.assertEqual(literal(0, self.R).term, REAL.zero)
        self.assertEqual(literal(1, self.R).term, REAL.one)
        self.assertEqual(literal(2, self.R).term, REAL.cast(numeral(2)))
        self.assertEqual(
            literal(-2, self.R).term, REAL.neg(REAL.cast(numeral(2)))
        )

    def test_definitions_report_no_axioms(self):
        self.assertEqual((self.x - 2 * self.y**3).axioms, ())

    def test_the_operations_do_not_reduce(self):
        """Nothing simplifies by itself: x + 0 is not x until a law says so."""
        t = self.x + 0
        self.assertEqual(self.nf(t), t.term)
        self.assertFalse(t.defeq(self.x))

    def test_laws_do_not_compute(self):
        p = cite(REAL.add_zero, self.x)
        self.assertEqual(self.nf(p), p.term)

    def test_powers_by_a_variable_exponent_are_stuck(self):
        """The definition unfolds, then the recursion has no numeral to
        select on, so it suspends rather than looping."""
        n = judge(N, SET, engine=self.engine).hyp("n")
        stuck = self.nf(self.x**n)
        self.assertEqual(stuck.fn, natrec)
        self.assertEqual(stuck.args[1], n.term)
        self.assertEqual(self.engine.nf(stuck), stuck)


class TestCiting(RingTest):
    def test_cite_instantiates_a_law(self):
        law = cite(REAL.mul_add, self.z, self.x, self.y)
        self.assertEqual(
            law.repr_unicode().split(" : ")[1], "z ⋅ (x + y) = z ⋅ x + z ⋅ y"
        )

    def test_cite_at_compound_terms(self):
        law = cite(REAL.add_comm, self.x * self.y, self.z**2)
        self.assertEqual(
            law.repr_unicode().split(" : ")[1], "x ⋅ y + z² = z² + x ⋅ y"
        )

    def test_citing_at_the_wrong_set_is_refused(self):
        n = judge(N, SET, engine=self.engine).hyp("n")
        with self.assertRaises(DerivationError) as raised:
            cite(REAL.add_comm, n, n)
        self.assertIn("Cannot cite", str(raised.exception))

    def test_citing_with_the_wrong_number_of_arguments_is_refused(self):
        with self.assertRaises(ArityError):
            cite(REAL.add_comm, self.x)


if __name__ == "__main__":
    unittest.main()
