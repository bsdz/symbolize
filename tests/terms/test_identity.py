"""The identity set and the rules derived from J ([BN] ch. 8, [ST] §5.3).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, Arrow, Cross, Var
from symbolize.terms.check import TypingError
from symbolize.terms.decl import SET
from symbolize.terms.derive import (DerivationError, cong, eq, family, forall,
                                    hyp, judge, prim, refl, set_var, symm,
                                    trans, transport)
from symbolize.terms.library import STANDARD, Id, J, N, numeral
from symbolize.terms.library import refl as refl_const
from symbolize.terms.library import zero


class IdentityTest(unittest.TestCase):
    def setUp(self):
        self.A, self.B = set_var("A"), set_var("B")
        self.N = judge(N, SET)
        self.a, self.b, self.c = (hyp(n, self.A) for n in ("a", "b", "c"))
        self.p = hyp("p", self.a.eq(self.b))
        self.q = hyp("q", self.b.eq(self.c))

    def assertChecks(self, j):
        """Re-verify a derived judgement with the type checker, since the
        rules build their conclusions with check=False."""
        j.engine.checker.check(j.ctx, j.term, j.type)

    def assertType(self, j, type_):
        self.assertTrue(j.has_type(type_), "%r, expected type %r" % (j, type_))
        self.assertChecks(j)


class TestFormation(IdentityTest):
    def test_is_a_set(self):
        s = eq(self.a, self.b)
        self.assertTrue(s.is_set)
        self.assertEqual(s.term, Id(self.A.term, self.a.term, self.b.term))
        self.assertEqual(self.a.eq(self.b), s)
        self.assertChecks(s)

    def test_endpoints_must_share_a_set(self):
        with self.assertRaises(DerivationError):
            eq(self.a, hyp("z", self.B))

    def test_formation_checks_its_premises(self):
        # Id(N, a, b) with a, b : A is not a set
        with self.assertRaises(TypingError):
            judge(Id(N, self.a.term, self.b.term), SET, self.b.ctx)

    def test_distinct_variables_still_form_a_set(self):
        """Propositional equality is weaker than definitional: a = b is a
        perfectly good set even though a and b are not definitionally
        equal (and so have no refl proof)."""
        self.assertFalse(self.a.defeq(self.b))
        self.assertTrue(self.a.eq(self.b).is_set)


class TestIntroduction(IdentityTest):
    def test_refl(self):
        r = refl(self.a)
        self.assertType(r, self.a.eq(self.a))
        self.assertEqual(r, self.a.refl)
        self.assertEqual(r.term, refl_const(self.a.term))

    def test_refl_absorbs_definitional_equality(self):
        """refl proves any two definitionally equal terms equal: the work is
        done by the evaluator, not by the identity set."""
        # a natrec that fires on its base case is definitionally succ(0)
        n = hyp("n", self.N)
        step = hyp("f", forall(n, self.N >> self.N))
        base = prim(judge(zero, N), judge(numeral(1), N), step)
        self.assertFalse(base.term == numeral(1))
        self.assertTrue(base.defeq(judge(numeral(1), N)))
        self.assertType(refl(base), eq(judge(numeral(1), N), base))

        # ((x)x)(a) is definitionally a. The checker cannot re-infer an
        # applied lambda (it carries no domain), so only the type is
        # compared here; the derivation layer supplies it.
        applied = self.a.abstract(self.a)(self.a)
        self.assertTrue(refl(applied).has_type(applied.eq(self.a)))
        self.assertTrue(refl(applied).has_type(self.a.eq(applied)))


class TestElimination(IdentityTest):
    def test_iota_rule(self):
        """J(C, refl(a), d) = d(a)"""
        C = Var("C", Arrow(Cross((A0, A0, A0)), A0))
        d = Var("d", Arrow(A0, A0))
        ev = self.a.engine.evaluator
        self.assertEqual(ev.nf(J(C, refl_const(self.a.term), d)), d(self.a.term))
        # stuck on a variable proof
        self.assertEqual(ev.whnf(J(C, self.p.term, d)), J(C, self.p.term, d))

    def test_symm(self):
        s = symm(self.p)
        self.assertType(s, self.b.eq(self.a))
        self.assertEqual(s, self.p.symm)
        with self.assertRaises(DerivationError):
            symm(self.a)  # not an identity proof

    def test_symm_computes_on_refl(self):
        self.assertEqual(self.a.refl.symm.run().term, refl_const(self.a.term))
        self.assertEqual(self.a.refl.symm.symm.run().term, refl_const(self.a.term))

    def test_trans(self):
        t = trans(self.p, self.q)
        self.assertType(t, self.a.eq(self.c))
        self.assertEqual(t, self.p.trans(self.q))

    def test_trans_checks_the_join(self):
        r = hyp("r", self.c.eq(self.a))
        with self.assertRaises(DerivationError):
            trans(self.p, r)  # p ends at b, r starts at c
        other = hyp("o", hyp("u", self.B).eq(hyp("v", self.B)))
        with self.assertRaises(DerivationError):
            trans(self.p, other)  # different sets

    def test_trans_computes_on_refl(self):
        # J recurses on the right-hand proof, so that is the side that fires
        self.assertEqual(trans(self.p, self.b.refl).run().term, self.p.term)
        self.assertEqual(
            trans(self.a.refl, self.a.refl).run().term, refl_const(self.a.term)
        )
        # with a variable on the right it is stuck, but still well typed
        stuck = trans(self.a.refl, self.p)
        self.assertType(stuck, self.a.eq(self.b))
        self.assertEqual(stuck.run().type, stuck.type)

    def test_cong(self):
        f = hyp("f", self.A >> self.B)
        r = cong(f, self.p)
        self.assertType(r, f(self.a).eq(f(self.b)))
        self.assertEqual(r, f.cong(self.p))
        self.assertEqual(cong(f, self.a.refl).run().term, refl_const(f(self.a).term))

    def test_cong_rejects_a_mismatched_function(self):
        g = hyp("g", self.B >> self.A)
        with self.assertRaises(DerivationError):
            cong(g, self.p)
        with self.assertRaises(DerivationError):
            cong(self.a, self.p)  # not a function
        # a dependent function has no single codomain for cong to use
        P = family("P", self.A)
        x = hyp("x", self.A)
        with self.assertRaises(DerivationError):
            cong(hyp("k", forall(x, P(x))), self.p)

    def test_transport(self):
        P = family("P", self.A)
        pa = hyp("pa", P(self.a))
        r = transport(P, self.p, pa)
        self.assertType(r, P(self.b))
        self.assertEqual(r, P.transport(self.p, pa))
        # along refl it is the identity
        self.assertEqual(transport(P, self.a.refl, pa).run().term, pa.term)

    def test_transport_rejects_bad_premises(self):
        P = family("P", self.A)
        Q = family("Q", self.B)
        pa = hyp("pa", P(self.a))
        with self.assertRaises(DerivationError):
            transport(Q, self.p, pa)  # family over the wrong set
        with self.assertRaises(DerivationError):
            transport(P, self.p, hyp("pb", P(self.b)))  # c is at the wrong end
        with self.assertRaises(DerivationError):
            transport(self.A, self.p, pa)  # not a family


class TestDerivedProofs(IdentityTest):
    """Small theorems proved here rather than imported."""

    def test_symm_is_an_involution_on_refl(self):
        self.assertEqual(self.a.refl.symm.symm.run(), self.a.refl.run())

    def test_congruence_of_succ(self):
        m, n = hyp("m", self.N), hyp("n", self.N)
        p = hyp("p", m.eq(n))
        s = hyp("s", self.N >> self.N)
        self.assertType(cong(s, p), s(m).eq(s(n)))

    def test_leibniz(self):
        """From a = b and P(a), derive P(b); and back again via symm."""
        P = family("P", self.A)
        pa = hyp("pa", P(self.a))
        pb = transport(P, self.p, pa)
        self.assertType(pb, P(self.b))
        back = transport(P, self.p.symm, pb)
        self.assertType(back, P(self.a))


class TestRendering(IdentityTest):
    def test_styles(self):
        s = self.a.eq(self.b)
        self.assertEqual(s.repr_latex(), "a = b")
        self.assertEqual(s.repr_unicode(), "a = b")
        self.assertEqual(s.repr_typestring(), "Id(A, a, b)")
        self.assertEqual(self.a.refl.repr_latex(), "refl(a) : a = a")

    def test_nested_equations_are_parenthesised(self):
        from symbolize.terms.derive import implies

        self.assertEqual(
            implies(self.a.eq(self.b), self.b.eq(self.a)).repr_latex(),
            r"(a = b) \Rightarrow (b = a)",
        )

    def test_numerals(self):
        s = eq(judge(numeral(1), N), judge(numeral(2), N))
        self.assertEqual(s.repr_unicode(), "succ(0) = succ(succ(0))")
        self.assertEqual(s.repr_typestring(), "Id(N, succ(0), succ(succ(0)))")


class TestRegistry(IdentityTest):
    def test_declared(self):
        for c in (Id, refl_const, J):
            self.assertIsNotNone(STANDARD.signature(c))
        self.assertTrue(STANDARD.is_constructor(refl_const))
        self.assertEqual(STANDARD.constructor_of(refl_const), Id)
        self.assertEqual(STANDARD.major(J), (1,))


if __name__ == "__main__":
    unittest.main()
