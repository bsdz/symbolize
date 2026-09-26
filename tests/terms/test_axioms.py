"""Axioms: statements believed rather than proved, and the tracking that
keeps them visible.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, Arrow, Const, Cross
from symbolize.terms.decl import SET, Provenance, axioms_used
from symbolize.terms.derive import (DerivationError, Engine, axiom, family,
                                    forall, hyp, judge, set_var)
from symbolize.terms.library import N, numeral, standard

LEAN = Provenance(
    "lean4", "4.23.0", "Nat.add_zero", "theorem Nat.add_zero (n : Nat) : n + 0 = n"
)


class AxiomTest(unittest.TestCase):
    def setUp(self):
        # a private registry: declaring axioms mutates it
        self.engine = Engine(standard())
        self.registry = self.engine.registry
        self.N = judge(N, SET, engine=self.engine)
        self.A = set_var("A", engine=self.engine)
        self.B = set_var("B", engine=self.engine)


class TestProvenance(unittest.TestCase):
    def test_digest_and_display(self):
        self.assertEqual(len(LEAN.digest), 16)
        self.assertEqual(LEAN.digest, Provenance(statement=LEAN.statement).digest)
        self.assertNotEqual(LEAN.digest, Provenance(statement="something else").digest)
        self.assertIn("lean4 4.23.0: Nat.add_zero", str(LEAN))
        self.assertIn(LEAN.digest, str(LEAN))

    def test_defaults(self):
        p = Provenance()
        self.assertEqual(p.system, "local")
        self.assertEqual(p.digest, "")
        self.assertEqual(str(p), "local")

    def test_immutable(self):
        with self.assertRaises(Exception):
            LEAN.system = "coq"


class TestDeclaration(AxiomTest):
    def test_closed_statement(self):
        n = hyp("n", self.N)
        stmt = forall(n, n.eq(n))
        ax = axiom("nat_refl", stmt, LEAN)
        self.assertTrue(ax.has_type(stmt))
        self.assertEqual(ax.term, Const("nat_refl"))
        self.assertTrue(self.registry.is_axiom(Const("nat_refl")))
        self.assertEqual(self.registry.provenance(Const("nat_refl")), LEAN)
        self.assertEqual(self.registry.axioms(), (Const("nat_refl"),))
        # and it is usable: instantiate the quantifier
        self.assertTrue(
            ax(judge(numeral(2), N, engine=self.engine)).has_type(
                judge(numeral(2), N, engine=self.engine).eq(
                    judge(numeral(2), N, engine=self.engine)
                )
            )
        )

    def test_statement_must_be_a_set(self):
        n = hyp("n", self.N)
        with self.assertRaises(DerivationError):
            axiom("bad", n)

    def test_redeclaration_is_refused(self):
        stmt = self.A >> self.A
        axiom("thing", stmt)
        with self.assertRaises(DerivationError):
            axiom("thing", stmt)

    def test_declared_axiom_is_type_checked_in_use(self):
        a = hyp("a", self.A)
        ax = axiom("a_implies_b", self.A >> self.B)
        self.assertTrue(ax(a).has_type(self.B))
        with self.assertRaises(DerivationError):
            ax(hyp("q", self.B))  # wrong argument type


class TestDependencies(AxiomTest):
    def test_set_variable_becomes_a_parameter(self):
        """An axiom stated over a variable set is a schema: the set is a
        parameter of the declaration, so it can be re-instantiated."""
        ax = axiom("double_negation", (~~self.A) >> self.A)
        const = Const("double_negation", Arrow(A0, A0))
        self.assertEqual(ax.term, const(self.A.term))
        self.assertTrue(self.registry.is_axiom(const))
        # instantiate the schema at N
        at_n = ax.subst(self.A, self.N)
        self.assertTrue(at_n.has_type((~~self.N) >> self.N))
        self.assertEqual(at_n.term, const(N))
        self.assertNotIn(self.A.term, at_n.ctx)

    def test_family_dependency(self):
        x = hyp("x", self.A)
        P = family("P", self.A, engine=self.engine)
        ax = axiom("p_self", forall(x, P(x) >> P(x)))
        const = Const("p_self", Arrow(Cross((A0, Arrow(A0, A0))), A0))
        self.assertEqual(ax.term, const(self.A.term, P.term))
        self.assertTrue(ax.has_type(forall(x, P(x) >> P(x))))
        signature = self.registry.signature(const)
        self.assertEqual(len(signature.params), 2)
        self.assertEqual(signature.params[1].hyps[0][1], signature.params[0].var)

    def test_only_mentioned_hypotheses_are_parameters(self):
        hyp("unused", self.B)
        ax = axiom("just_a", self.A >> self.A)
        self.assertEqual(ax.term, Const("just_a", Arrow(A0, A0))(self.A.term))


class TestOpacity(AxiomTest):
    def test_axiom_does_not_compute(self):
        ax = axiom("opaque", self.A >> self.A)
        a = hyp("a", self.A)
        applied = ax(a)
        self.assertEqual(applied.run().term, applied.term)
        self.assertEqual(self.engine.whnf(ax.term), ax.term)

    def test_axiom_has_no_rules_or_definition(self):
        axiom("opaque", self.A)
        const = Const("opaque", Arrow(A0, A0))
        self.assertEqual(self.registry.rules(const), ())
        self.assertIsNone(self.registry.definition(const))
        self.assertIsNotNone(self.registry.signature(const))


class TestTracking(AxiomTest):
    def test_proved_judgement_reports_nothing(self):
        a = hyp("a", self.A)
        self.assertEqual(a.abstract(a).axioms, ())
        self.assertEqual(a.refl.axioms, ())
        self.assertIn("no axioms", a.refl.trust_report())

    def test_axiom_is_reported_where_used(self):
        a = hyp("a", self.A)
        ax = axiom("jump", self.A >> self.B)
        used = ax(a).abstract(a)
        self.assertEqual([c.name for c in used.axioms], ["jump"])
        report = used.trust_report()
        self.assertIn("1 axiom", report)
        self.assertIn("jump", report)
        self.assertIn("local", report)

    def test_provenance_appears_in_the_report(self):
        n = hyp("n", self.N)
        ax = axiom("add_zero", forall(n, n.eq(n)), LEAN)
        report = ax.trust_report()
        self.assertIn("lean4 4.23.0: Nat.add_zero", report)
        self.assertIn(LEAN.digest, report)

    def test_definitions_are_unfolded(self):
        """An axiom reached only through an abbreviation is still reported."""
        ax = axiom("hidden", self.A)
        alias = Const("alias", Arrow(A0, A0))
        self.registry.define(alias, ax.term.abstract(self.A.term))
        self.assertEqual(
            axioms_used(alias(self.B.term), self.registry),
            (Const("hidden", Arrow(A0, A0)),),
        )

    def test_several_axioms_are_sorted(self):
        a = hyp("a", self.A)
        zeta = axiom("zeta", self.A >> self.B)
        alpha = axiom("alpha", self.B >> self.A)
        combined = alpha(zeta(a))
        self.assertTrue(combined.has_type(self.A))
        self.assertEqual([c.name for c in combined.axioms], ["alpha", "zeta"])
        self.assertEqual([c.name for c in self.registry.axioms()], ["alpha", "zeta"])
        self.assertIn("2 axiom", combined.trust_report())

    def test_tracking_is_per_registry(self):
        axiom("only_here", self.A)
        other = Engine(standard())
        self.assertEqual(other.registry.axioms(), ())


if __name__ == "__main__":
    unittest.main()
