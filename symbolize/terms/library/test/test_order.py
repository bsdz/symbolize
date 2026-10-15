"""The order on N: unfolding, proofs, and the extractable difference.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import Var
from symbolize.terms.check import TypingError
from symbolize.terms.decl import SET
from symbolize.terms.derive import (
    Engine,
    cong_in,
    eq,
    fst,
    hyp,
    judge,
    pair,
    prim,
    refl,
)
from symbolize.terms.library import (
    Id,
    N,
    Sigma,
    add,
    ge,
    gt,
    le,
    lt,
    numeral,
    standard,
    succ,
    zero,
)


class OrderTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard())
        self.N = judge(N, SET, engine=self.engine)

    def nat(self, term, ctx=None):
        return judge(term, N, ctx or self.N.ctx, engine=self.engine)

    def nf(self, term):
        return self.engine.evaluator.nf(term)

    def whnf(self, term):
        return self.engine.evaluator.whnf(term)


class TestDefinitions(OrderTest):
    def test_le_unfolds_to_a_sigma(self):
        k = Var("k")
        self.assertEqual(
            self.whnf(le(numeral(1), numeral(2))),
            Sigma(
                N,
                Id(N, add(numeral(1), k), numeral(2)).abstract(k),
            ),
        )

    def test_lt_is_succ_le(self):
        self.assertEqual(
            self.whnf(lt(numeral(1), numeral(2))),
            self.whnf(le(succ(numeral(1)), numeral(2))),
        )

    def test_ge_and_gt_swap_their_arguments(self):
        a, b = numeral(1), numeral(2)
        self.assertEqual(self.whnf(ge(a, b)), self.whnf(le(b, a)))
        self.assertEqual(self.whnf(gt(a, b)), self.whnf(lt(b, a)))

    def test_each_relation_is_a_set(self):
        for rel in (le, lt, ge, gt):
            with self.subTest(rel.name):
                self.engine.checker.is_set(
                    self.N.ctx, rel(numeral(1), numeral(2))
                )

    def test_a_relation_needs_naturals(self):
        with self.assertRaises(TypingError):
            self.engine.checker.is_set(self.N.ctx, le(N, numeral(1)))


class TestReflexivity(OrderTest):
    """``n ≤ n`` holds by computation, with no induction.

    ``add`` recurses on its second argument, so ``add(n, 0)`` reduces to
    ``n``; the witness is ``0`` and the equation is ``refl``. This is the
    reason for the orientation ``m + k = n`` in the definition.
    """

    def test_le_refl_for_a_variable(self):
        n = hyp("n", self.N)
        proof = judge(
            pair(self.nat(zero), refl(self.nat(n.term, n.ctx))).term,
            le(n.term, n.term),
            n.ctx,
            engine=self.engine,
        )
        self.assertTrue(proof.has_type(le(n.term, n.term)))
        self.assertEqual(proof.axioms, ())
        self.assertEqual(self.nf(fst(proof).term), zero)

    def test_le_refl_generalises(self):
        n = hyp("n", self.N)
        proof = judge(
            pair(self.nat(zero), refl(self.nat(n.term, n.ctx))).term,
            le(n.term, n.term),
            n.ctx,
            engine=self.engine,
        )
        theorem = proof.abstract(n)
        self.assertEqual(theorem.repr_unicode().split(" : ")[1], "∀n.(n ≤ n)")
        self.engine.checker.check(theorem.ctx, theorem.term, theorem.type)


class TestConcreteNumerals(OrderTest):
    def test_two_le_five_with_its_difference(self):
        five = self.nat(numeral(5))
        proof = judge(
            pair(self.nat(numeral(3)), five.refl).term,
            le(numeral(2), numeral(5)),
            engine=self.engine,
        )
        self.assertEqual(self.nf(fst(proof).term), numeral(3))

    def test_a_wrong_witness_is_refused(self):
        """2 + 1 is not 5, so the pair does not typecheck."""
        with self.assertRaises(TypingError):
            judge(
                pair(self.nat(numeral(1)), self.nat(numeral(5)).refl).term,
                le(numeral(2), numeral(5)),
                engine=self.engine,
            )

    def test_two_lt_five(self):
        proof = judge(
            pair(self.nat(numeral(2)), self.nat(numeral(5)).refl).term,
            lt(numeral(2), numeral(5)),
            engine=self.engine,
        )
        self.assertTrue(proof.has_type(lt(numeral(2), numeral(5))))

    def test_five_gt_two(self):
        proof = judge(
            pair(self.nat(numeral(2)), self.nat(numeral(5)).refl).term,
            gt(numeral(5), numeral(2)),
            engine=self.engine,
        )
        self.assertTrue(proof.has_type(gt(numeral(5), numeral(2))))

    def test_a_false_inequality_has_no_such_witness(self):
        """5 ≤ 2 would need k with 5 + k = 2; no numeral works."""
        for k in range(4):
            with self.subTest(k=k):
                with self.assertRaises(TypingError):
                    judge(
                        pair(
                            self.nat(numeral(k)), self.nat(numeral(2)).refl
                        ).term,
                        le(numeral(5), numeral(2)),
                        engine=self.engine,
                    )


class TestZeroIsLeast(OrderTest):
    """``∀n. 0 ≤ n`` needs the induction proof of ``0 + n = n``."""

    def zero_add(self):
        n = hyp("n", self.N)
        x = hyp("x", self.N)
        ih = hyp("ih", eq(self.nat(add(zero, x.term), x.ctx), x))
        s = Var("s")
        step = cong_in(succ(s).abstract(s), ih).abstract(ih).abstract(x)
        return prim(n, refl(self.nat(zero)), step).abstract(n)

    def test_zero_le_n(self):
        n = hyp("n", self.N)
        theorem = judge(
            pair(n, self.zero_add().apply(n)).term,
            le(zero, n.term),
            n.ctx,
            engine=self.engine,
        ).abstract(n)
        self.assertEqual(
            theorem.repr_unicode().split(" : ")[1], "∀n.(0 ≤ n)"
        )
        self.assertEqual(theorem.axioms, ())
        # independently re-checked, not merely built by the rules
        self.engine.checker.check(theorem.ctx, theorem.term, theorem.type)

    def test_the_difference_at_a_numeral_is_the_number(self):
        n = hyp("n", self.N)
        theorem = judge(
            pair(n, self.zero_add().apply(n)).term,
            le(zero, n.term),
            n.ctx,
            engine=self.engine,
        ).abstract(n)
        for k in (0, 1, 4):
            with self.subTest(k=k):
                at = theorem.apply(self.nat(numeral(k)))
                self.assertEqual(self.nf(fst(at).term), numeral(k))


class TestRendering(OrderTest):
    def test_styles(self):
        t = le(numeral(1), numeral(2))
        self.assertEqual(t.repr_typestring(), "le(succ(0), succ(succ(0)))")
        self.assertEqual(t.repr_unicode(), "succ(0) ≤ succ(succ(0))")
        self.assertEqual(t.repr_latex(), r"succ(0) \leq succ(succ(0))")

    def test_each_symbol(self):
        a, b = numeral(0), numeral(1)
        self.assertEqual(le(a, b).repr_unicode(), "0 ≤ succ(0)")
        self.assertEqual(lt(a, b).repr_unicode(), "0 < succ(0)")
        self.assertEqual(ge(a, b).repr_unicode(), "0 ≥ succ(0)")
        self.assertEqual(gt(a, b).repr_unicode(), "0 > succ(0)")


if __name__ == "__main__":
    unittest.main()
