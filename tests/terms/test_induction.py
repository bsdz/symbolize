"""A worked proof by induction: 0 + n = n.

This exercises the whole stack at once -- natrec for the induction, Id and J
for the equation, and the type checker as an independent referee -- so it is
kept as a regression test as well as an example.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import Var
from symbolize.terms.decl import SET
from symbolize.terms.derive import (Argument, Engine, cong_in, eq, hyp, judge,
                                    prim, refl)
from symbolize.terms.library import N, add, numeral, standard, succ, zero


class TestZeroAdd(unittest.TestCase):
    """0 + n = n.

    ``add`` recurses on its second argument, so ``n + 0`` reduces to ``n``
    by computation but ``0 + n`` does not: this one needs induction.
    """

    def setUp(self):
        self.engine = Engine(standard())
        self.N = judge(N, SET, engine=self.engine)

    def nat(self, term, ctx=None):
        return judge(term, N, ctx or self.N.ctx, engine=self.engine)

    def prove(self):
        """Build the proof, returning it with its parts."""
        n = hyp("n", self.N)

        # base case: 0 + 0 = 0 holds by computation
        base = refl(self.nat(zero))

        # step: from  ih : 0 + x = x  conclude  0 + succ x = succ x,
        # by congruence under succ
        x = hyp("x", self.N)
        ih = hyp("ih", eq(self.nat(add(zero, x.term), x.ctx), x))
        s = Var("s")
        step = cong_in(succ(s).abstract(s), ih)

        f = step.abstract(ih).abstract(x)
        theorem = prim(n, base, f).abstract(n)
        return theorem, n, base, step, ih

    def test_the_statement_needs_induction(self):
        n = hyp("n", self.N)
        left = self.nat(add(zero, n.term), n.ctx)
        self.assertFalse(left.defeq(n))  # 0 + n is stuck
        # whereas the mirror image is definitional
        right = self.nat(add(n.term, zero), n.ctx)
        self.assertTrue(right.defeq(n))
        self.assertEqual(right.refl.axioms, ())

    def test_base_case(self):
        base = refl(self.nat(zero))
        goal = eq(self.nat(add(zero, zero)), self.nat(zero))
        self.assertTrue(base.has_type(goal))

    def test_step_case(self):
        x = hyp("x", self.N)
        ih = hyp("ih", eq(self.nat(add(zero, x.term), x.ctx), x))
        s = Var("s")
        step = cong_in(succ(s).abstract(s), ih)
        self.assertEqual(step.repr_unicode().split(" : ")[1], "succ(0 + x) = succ(x)")
        # which is exactly the motive at succ(x)
        goal = eq(
            self.nat(add(zero, succ(x.term)), x.ctx),
            self.nat(succ(x.term), x.ctx),
        )
        self.assertTrue(step.has_type(goal))

    def test_theorem(self):
        theorem, n, _, _, _ = self.prove()
        self.assertEqual(theorem.type.repr_unicode(), "∀n.(0 + n) = n")
        self.assertEqual(theorem.type.repr_latex(), r"\forall{n}.(0 + n) = n")
        self.assertNotIn(n.term, theorem.ctx)

    def test_it_rests_on_no_axioms(self):
        theorem, _, _, _, _ = self.prove()
        self.assertEqual(theorem.axioms, ())
        self.assertIn("no axioms", theorem.trust_report())

    def test_the_checker_agrees(self):
        """The rules built the conclusion; the checker re-verifies the term."""
        theorem, _, _, _, _ = self.prove()
        self.engine.checker.check(theorem.ctx, theorem.term, theorem.type)

    def test_instances(self):
        theorem, _, _, _, _ = self.prove()
        for k in (0, 1, 3):
            instance = theorem(self.nat(numeral(k)))
            goal = eq(self.nat(add(zero, numeral(k))), self.nat(numeral(k)))
            self.assertTrue(instance.has_type(goal))
            # the proof is a program: it computes to a reflexivity proof
            self.assertEqual(
                instance.run().term.repr_typestring(),
                "refl(%s)" % (numeral(k).repr_typestring(),),
            )

    def test_renders_as_a_derivation(self):
        theorem, n, base, step, ih = self.prove()
        tree = Argument(
            [
                Argument([], base, label=r"\mathrm{refl}"),
                Argument([ih], step, discharges=[ih], label=r"\mathrm{cong}"),
            ],
            theorem,
            discharges=[n],
            label=r"\mathrm{natrec}",
        )
        latex = tree.repr_latex()
        self.assertIn(r"\forall{n}.(0 + n) = n", latex)
        self.assertIn(r"\mathrm{natrec}", latex)
        self.assertIn("[n : \\mathbb{N}]", latex)


if __name__ == "__main__":
    unittest.main()
