"""Arithmetic operators on judgements, and symbolic proofs written with them.

The operators live on ``Judgement`` (derive.py) and dispatch through the
``Operators`` registered for the operand's set (decl.py), so this spans
both modules.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import Var
from symbolize.terms.check import TypingError
from symbolize.terms.decl import SET, DeclarationError, Operators, Signature
from symbolize.terms.derive import (
    DerivationError,
    Engine,
    add,
    cite,
    eq,
    judge,
    literal,
    mul,
    refl,
    set_var,
    symbols,
)
from symbolize.terms.library import (
    REAL,
    N,
    R,
)
from symbolize.terms.library import add as nat_add
from symbolize.terms.library import mul as nat_mul
from symbolize.terms.library import (
    numeral,
    standard,
    succ,
)


class ArithmeticTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard(reals=True))
        self.R = judge(R, SET, engine=self.engine)
        self.x, self.y, self.z = symbols("x y z", self.R)

    def show_set(self, j):
        return j.repr_unicode()

    def show(self, j):
        return j.repr_unicode().split(" : ")[1]


class TestBuilding(ArithmeticTest):
    def test_operators_build_the_term_and_nothing_more(self):
        t = (self.x + 1) * self.y
        self.assertEqual(
            t.term, REAL.mul(REAL.add(self.x.term, REAL.one), self.y.term)
        )
        self.assertEqual(t.type, R)

    def test_every_operator(self):
        x, y = self.x, self.y
        cases = [
            (x + y, REAL.add(x.term, y.term)),
            (x * y, REAL.mul(x.term, y.term)),
            (x - y, REAL.sub(x.term, y.term)),
            (-x, REAL.neg(x.term)),
            (x**3, REAL.pow(x.term, numeral(3))),
        ]
        for built, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(built.term, expected)

    def test_int_literals_on_either_side(self):
        self.assertEqual(
            (self.x + 2).term, REAL.add(self.x.term, REAL.cast(numeral(2)))
        )
        self.assertEqual(
            (2 + self.x).term, REAL.add(REAL.cast(numeral(2)), self.x.term)
        )
        self.assertEqual((0 * self.x).term, REAL.mul(REAL.zero, self.x.term))
        self.assertEqual((1 - self.x).term, REAL.sub(REAL.one, self.x.term))

    def test_negative_literals_are_negations(self):
        self.assertEqual(
            (self.x + -3).term,
            REAL.add(self.x.term, REAL.neg(REAL.cast(numeral(3)))),
        )

    def test_contexts_merge(self):
        t = self.x * self.y + self.z
        self.assertEqual(sorted(t.ctx.names()), ["x", "y", "z"])

    def test_the_result_type_checks(self):
        t = (self.x + 1) ** 2 - 2 * self.x * self.y
        self.engine.checker.check(t.ctx, t.term, t.type)

    def test_function_forms(self):
        self.assertEqual(add(self.x, 1), self.x + 1)
        self.assertEqual(mul(2, self.y), 2 * self.y)

    def test_an_element_of_n_as_exponent(self):
        n = judge(N, SET, engine=self.engine).hyp("n")
        self.assertEqual((self.x**n).term, REAL.pow(self.x.term, n.term))


class TestEquations(ArithmeticTest):
    """An equation's side may be a literal or a bare term of the other's
    set, so ``(x + 1).eq(0)`` needs no ``literal(0, R)``."""

    def test_an_int_literal(self):
        e = ((self.x + 1) ** 2 - 2 * self.x * self.y).eq(0)
        self.assertEqual(self.show_set(e), "(x + 1)² - 2 ⋅ x ⋅ y = 0")
        self.assertEqual(e.term.args[2], REAL.zero)

    def test_a_literal_on_the_left(self):
        e = eq(2, self.x)
        self.assertEqual(self.show_set(e), "2 = x")

    def test_a_bare_term(self):
        self.assertEqual(self.x.eq(REAL.zero), self.x.eq(0))
        e = self.x.eq(REAL.add(self.x.term, REAL.one))
        self.assertEqual(self.show_set(e), "x = x + 1")

    def test_a_bare_term_of_another_set_is_refused(self):
        with self.assertRaises(TypingError):
            self.x.eq(numeral(0))

    def test_refusals(self):
        for a, b in [(0, 0), (self.x, "0"), (self.x, True)]:
            with self.subTest(a=a, b=b):
                with self.assertRaises(DerivationError):
                    eq(a, b)


class TestSymbols(ArithmeticTest):
    def test_one_name_gives_one_judgement(self):
        a = symbols("a", self.R)
        self.assertEqual(a.term, Var("a"))
        self.assertEqual(a.type, R)

    def test_names_split_on_spaces_and_commas(self):
        names = [j.term.name for j in symbols("a, b c", self.R)]
        self.assertEqual(names, ["a", "b", "c"])

    def test_no_names_is_refused(self):
        with self.assertRaises(DerivationError):
            symbols(" ,", self.R)


class TestNaturals(ArithmeticTest):
    """N has addition and multiplication but no subtraction: Lean's ``Nat.sub``
    truncates, a junk value AGENTS.md says not to import without thought."""

    def setUp(self):
        super().setUp()
        self.n = judge(N, SET, engine=self.engine).hyp("n")

    def test_addition_and_literals(self):
        self.assertEqual(
            (self.n + 1).term, nat_add(self.n.term, succ(numeral(0)))
        )
        self.assertEqual((self.n + 1).term.repr_unicode(), "n + succ(0)")

    def test_naturals_compute(self):
        two = literal(2, judge(N, SET, engine=self.engine))
        self.assertEqual(self.engine.nf((two * 3).term), numeral(6))

    def test_what_n_lacks(self):
        for label, build in [
            ("subtraction", lambda: self.n - 1),
            ("negation", lambda: -self.n),
            ("powers", lambda: self.n**2),
        ]:
            with self.subTest(label):
                with self.assertRaises(DerivationError) as raised:
                    build()
                self.assertIn(label, str(raised.exception))

    def test_negative_literal_is_refused(self):
        with self.assertRaises(DeclarationError):
            self.n + -1


class TestRefusals(ArithmeticTest):
    def test_mixing_sets(self):
        n = judge(N, SET, engine=self.engine).hyp("n")
        with self.assertRaises(DerivationError):
            self.x + n

    def test_sets_are_not_numbers(self):
        with self.assertRaises(DerivationError) as raised:
            self.R + self.R
        self.assertIn("is a set", str(raised.exception))

    def test_a_set_without_arithmetic(self):
        a = set_var("A", engine=self.engine).hyp("a")
        with self.assertRaises(DerivationError) as raised:
            a + 1
        self.assertIn("No arithmetic is declared on A", str(raised.exception))

    def test_other_python_values(self):
        for other in ("a", 1.5, True, None):
            with self.subTest(other=other):
                with self.assertRaises(TypeError):
                    self.x + other

    def test_negative_exponent(self):
        with self.assertRaises(DerivationError):
            self.x**-1

    def test_reals_must_be_declared(self):
        with self.assertRaises(TypingError):
            judge(R, SET, engine=Engine(standard()))


class TestOperatorTable(unittest.TestCase):
    """``Registry.add_operators`` checks the shapes it is given, which is what
    lets the operators skip re-checking every term they build."""

    def setUp(self):
        self.registry = standard()

    def test_n_has_operators(self):
        ops = self.registry.operators(N)
        self.assertEqual((ops.add, ops.mul, ops.neg), (nat_add, nat_mul, None))

    def test_a_carrier_is_registered_once(self):
        ops = self.registry.operators(N)
        with self.assertRaises(DeclarationError):
            self.registry.add_operators(ops)

    def test_undeclared_operation_is_refused(self):
        bogus = Operators(R, REAL.add, REAL.mul, numeral=lambda k: REAL.zero)
        with self.assertRaises(DeclarationError) as raised:
            self.registry.add_operators(bogus)
        self.assertIn("must be declared", str(raised.exception))

    def test_wrong_shape_is_refused(self):
        """N's addition is not an operation on R."""
        registry = standard()
        registry.declare(R, Signature((), SET))
        with self.assertRaises(DeclarationError) as raised:
            registry.add_operators(
                Operators(R, nat_add, nat_add, numeral=numeral)
            )
        self.assertIn("does not have the shape", str(raised.exception))


class TestSymbolicProof(ArithmeticTest):
    """Equations proved from the ring laws: each step is a law or a rewrite,
    and the result is re-checked independently of the rules that built it."""

    def recheck(self, p):
        self.engine.checker.check(p.ctx, p.term, p.type)

    def test_distributing_on_the_right(self):
        x, y, z = self.x, self.y, self.z
        p = cite(REAL.mul_comm, x + y, z).trans(cite(REAL.mul_add, z, x, y))
        self.assertEqual(self.show(p), "(x + y) ⋅ z = z ⋅ x + z ⋅ y")
        self.recheck(p)
        self.assertEqual(p.axioms, (REAL.mul_add, REAL.mul_comm))

    def test_simplifying_by_rewriting(self):
        """x + y + 0 = y + x: start from reflexivity and rewrite the right
        side one law at a time, as a simplifier would."""
        x, y = self.x, self.y
        e = x + y + 0
        p = refl(e)
        p = p.rw(cite(REAL.add_zero, x + y), at=[1])
        self.assertEqual(self.show(p), "x + y + 0 = x + y")
        p = p.rw(cite(REAL.add_comm, x, y), at=[1])
        self.assertEqual(self.show(p), "x + y + 0 = y + x")
        self.recheck(p)
        self.assertEqual(p.axioms, (REAL.add_comm, REAL.add_zero))

    def test_zero_add_is_a_theorem_not_an_axiom(self):
        """The mirrored law follows from add_comm and add_zero."""
        x = self.x
        p = cite(REAL.add_comm, literal(0, self.R), x).trans(
            cite(REAL.add_zero, x)
        )
        self.assertEqual(self.show(p), "0 + x = x")
        theorem = p.abstract(x)
        # an equation under ∀ is unbracketed, as the Lean import tests pin
        self.assertEqual(self.show(theorem), "∀x.0 + x = x")
        self.recheck(theorem)

    def test_trust_report_names_the_laws(self):
        p = cite(REAL.mul_comm, self.x, self.y)
        report = p.trust_report()
        self.assertIn("depends on 1 axiom(s)", report)
        self.assertIn("R.mul_comm", report)


if __name__ == "__main__":
    unittest.main()
