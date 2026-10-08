"""Rewriting with identity proofs, and the substitution notation for a
suspended one.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, App, Arrow, Var
from symbolize.terms.decl import SET, Provenance
from symbolize.terms.derive import (DerivationError, Engine, axiom, family,
                                    forall, hyp, judge, motive_for,
                                    occurrences, rewrite, set_var)
from symbolize.terms.library import N, implies, numeral, standard, succ, zero


class RewriteTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard())
        self.A = set_var("A", engine=self.engine)
        self.B = set_var("B", engine=self.engine)
        self.N = judge(N, SET, engine=self.engine)
        self.a, self.b, self.c = (hyp(n, self.A) for n in ("a", "b", "c"))
        self.p = hyp("p", self.a.eq(self.b))
        self.P = family("P", self.A, engine=self.engine)

    def assertChecks(self, j):
        j.engine.checker.check(j.ctx, j.term, j.type)

    def assertType(self, j, type_):
        self.assertTrue(j.has_type(type_), "%r, expected %r" % (j, type_))
        self.assertChecks(j)


class TestOccurrences(RewriteTest):
    def test_counting(self):
        f = Var("f", Arrow(A0, A0))
        a = self.a.term
        self.assertEqual(occurrences(a, a), 1)
        self.assertEqual(occurrences(f(a), a), 1)
        self.assertEqual(occurrences(implies(f(a), a), a), 2)
        self.assertEqual(occurrences(self.b.term, a), 0)
        # a match is not searched inside itself
        self.assertEqual(occurrences(f(a), f(a)), 1)

    def test_counting_under_binders(self):
        x = Var("x")
        body = implies(self.P(self.a).term, self.P(self.a).term).abstract(x)
        self.assertEqual(occurrences(body, self.a.term), 2)


class TestMotive(RewriteTest):
    def test_all_occurrences(self):
        z = Var("z")
        a = self.a.term
        fam = motive_for(implies(self.P(self.a).term, a), a, z)
        self.assertEqual(occurrences(fam, a), 0)
        self.assertEqual(fam, implies(self.P.term(z), z).abstract(z))

    def test_selected_occurrences(self):
        z = Var("z")
        a = self.a.term
        target = implies(self.P.term(a), a)
        first = motive_for(target, a, z, at=[0])
        second = motive_for(target, a, z, at=[1])
        self.assertEqual(first, implies(self.P.term(z), a).abstract(z))
        self.assertEqual(second, implies(self.P.term(a), z).abstract(z))

    def test_out_of_range_selection(self):
        z = Var("z")
        with self.assertRaises(DerivationError) as raised:
            motive_for(self.P.term(self.a.term), self.a.term, z, at=[0, 3])
        self.assertIn("only 1 occurrence", str(raised.exception))


class TestRewrite(RewriteTest):
    def test_rewrites_the_type(self):
        pa = hyp("pa", self.P(self.a))
        r = rewrite(pa, self.p)
        self.assertType(r, self.P(self.b))
        self.assertEqual(r, pa.rewrite(self.p))
        self.assertEqual(r, pa.rw(self.p))

    def test_rewrites_every_occurrence(self):
        both = hyp("h", self.P(self.a) >> self.P(self.a))
        r = rewrite(both, self.p)
        self.assertType(r, self.P(self.b) >> self.P(self.b))

    def test_selected_occurrence(self):
        both = hyp("h", self.P(self.a) >> self.P(self.a))
        self.assertType(rewrite(both, self.p, at=[0]), self.P(self.b) >> self.P(self.a))
        self.assertType(rewrite(both, self.p, at=[1]), self.P(self.a) >> self.P(self.b))

    def test_right_to_left_is_symm(self):
        pb = hyp("pb", self.P(self.b))
        self.assertType(rewrite(pb, self.p.symm), self.P(self.a))

    def test_round_trip(self):
        pa = hyp("pa", self.P(self.a))
        there = rewrite(pa, self.p)
        back = rewrite(there, self.p.symm)
        self.assertType(back, self.P(self.a))

    def test_refuses_when_the_pattern_is_absent(self):
        pc = hyp("pc", self.P(self.c))
        with self.assertRaises(DerivationError) as raised:
            rewrite(pc, self.p)
        self.assertIn("nothing to rewrite", str(raised.exception))

    def test_rewriting_with_refl_is_the_identity(self):
        pa = hyp("pa", self.P(self.a))
        r = rewrite(pa, self.a.refl)
        self.assertType(r, self.P(self.a))
        self.assertEqual(r.run().term, pa.term)

    def test_computes_on_a_concrete_identity(self):
        """With refl the transport reduces away, leaving the original proof."""
        Q = family("Q", self.N, engine=self.engine)
        two = judge(numeral(2), N, engine=self.engine)
        q = hyp("q", Q(two))
        r = rewrite(q, two.refl)
        self.assertEqual(r.run().term, q.term)

    def test_refuses_a_non_identity_proof(self):
        pa = hyp("pa", self.P(self.a))
        n = hyp("n", self.N)
        with self.assertRaises(DerivationError) as raised:
            rewrite(pa, hyp("w", forall(n, n.eq(n))))  # a Pi, not an Id
        self.assertIn("not a proof of an identity", str(raised.exception))
        with self.assertRaises(DerivationError):
            rewrite(pa, self.a)

    def test_the_motive_is_checked(self):
        """``rewrite`` verifies the abstracted statement really is a family
        over A before transporting, so an ill-typed rewrite is refused
        rather than yielding a judgement that does not hold. With only
        one-argument families in the library this is insurance for indexed
        families later; here it simply passes."""
        pa = hyp("pa", self.P(self.a))
        r = rewrite(pa, self.p)
        z = Var("z")
        fam = motive_for(pa.type, self.a.term, z)
        inner = merge_ctx = r.ctx.extend(z, self.A.term)
        self.engine.checker.is_set(merge_ctx, self.P.term(z))
        self.assertIsNotNone(inner)
        self.assertEqual(fam, self.P.term(z).abstract(z))

    def test_axiom_provenance_survives_a_rewrite(self):
        """A rewrite with an imported equation records the import."""
        n = hyp("n", self.N)
        stmt = forall(n, n.eq(n))
        imported = axiom(
            "nat_self",
            stmt,
            Provenance("lean4", "4.23.0", "Eq.refl", "theorem Eq.refl : a = a"),
        )
        two = judge(numeral(2), N, engine=self.engine)
        Q = family("Q", self.N, engine=self.engine)
        q = hyp("q", Q(two))
        r = rewrite(q, imported(two))
        self.assertType(r, Q(two))
        self.assertEqual([c.name for c in r.axioms], ["nat_self"])
        self.assertIn("lean4", r.trust_report())

    def test_rewrite_under_a_binder(self):
        x = hyp("x", self.A)
        f = hyp("f", forall(x, self.P(self.a)))
        r = rewrite(f, self.p)
        self.assertType(r, forall(x, self.P(self.b)))


class TestSubstitutionNotation(RewriteTest):
    def setUp(self):
        super().setUp()
        self.x, self.y = Var("x"), Var("y")
        self.redex = App(self.P.term(self.x).abstract(self.x), (self.a.term,))

    def test_pretty_styles_use_brackets(self):
        self.assertEqual(self.redex.repr_unicode(), "P(x)[x ≔ a]")
        self.assertEqual(self.redex.repr_latex(), r"P(x)[x \mathrel{\vcenter{:}}= a]")

    def test_typestring_stays_structural(self):
        self.assertEqual(self.redex.repr_typestring(), "((x)P(x))(a)")

    def test_several_binders(self):
        term = App(
            implies(self.P.term(self.x), self.P.term(self.y)).abstract(self.x, self.y),
            (self.a.term, self.b.term),
        )
        self.assertEqual(term.repr_unicode(), "(P(x) ⟹ P(y))[x ≔ a, y ≔ b]")

    def test_equal_to_its_reduct(self):
        """The bracket form is display only: it is the same term as before,
        and definitionally the substituted one."""
        self.assertTrue(self.engine.defeq(self.redex, self.P.term(self.a.term)))
        self.assertEqual(self.engine.whnf(self.redex), self.P.term(self.a.term))

    def test_lambda_is_not_a_substitution(self):
        from symbolize.terms.library import lam

        self.assertEqual(lam(self.x.abstract(self.x)).repr_unicode(), "λ(x).x")

    def test_mismatched_arities_show_the_application(self):
        """Beta adapts a multi-binder to a single pair argument; that is not
        written as a substitution."""
        two = implies(self.P.term(self.x), self.P.term(self.y)).abstract(self.x, self.y)
        term = App(two, (Var("r", two.arity.lhs),))
        self.assertTrue(term.repr_unicode().startswith("((x, y)"))


class TestNaturalExample(RewriteTest):
    """The shape a CAS identity would take: rewrite with an imported law."""

    def test_rewrite_with_an_imported_law(self):
        n = hyp("n", self.N)
        # imported:  forall n, succ(n) = succ(n)   (a stand-in for a real law)
        law = axiom(
            "succ_cong",
            forall(n, judge(succ(n.term), N, n.ctx).eq(judge(succ(n.term), N, n.ctx))),
            Provenance("lean4", "4.23.0", "Nat.succ.injEq"),
        )
        zero_j = judge(zero, N, engine=self.engine)
        Q = family("Q", self.N, engine=self.engine)
        q = hyp("q", Q(judge(succ(zero), N, engine=self.engine)))
        r = rewrite(q, law(zero_j))
        self.assertType(r, Q(judge(succ(zero), N, engine=self.engine)))
        self.assertEqual([c.name for c in r.axioms], ["succ_cong"])


if __name__ == "__main__":
    unittest.main()
