"""Commutative rings, declared axiomatically over a carrier.

There are no universes, so a ring cannot be a term -- a record of a set and
its operations that a theorem could quantify over. A ring is instead a
family of constants named after its carrier (``R.add``, ``R.add_comm``, ...)
declared into a registry, and a lemma about rings is proved once per
carrier. Universes would let it be proved once (AGENTS.md roadmap step 5).

What is believed and what is defined:

- The carrier and the operations ``0``, ``1``, ``+``, ``⋅``, ``-`` are
  primitive constants: typed, with no definition and no computation rules,
  so they never reduce. Postulating them is harmless -- any inhabited set
  with any operations is a model -- so they are not recorded as axioms.
- The eight laws are axioms, each with its ``Provenance``, so a derivation
  that relies on one reports it (``Judgement.trust_report``). They are the
  usual presentation, with Mathlib's names:

      add_assoc       (a + b) + c = a + (b + c)
      add_comm        a + b = b + a
      add_zero        a + 0 = a
      add_neg_cancel  a + -a = 0
      mul_assoc       (a ⋅ b) ⋅ c = a ⋅ (b ⋅ c)
      mul_comm        a ⋅ b = b ⋅ a
      mul_one         a ⋅ 1 = a
      mul_add         a ⋅ (b + c) = a ⋅ b + a ⋅ c

  The mirrored laws (``zero_add``, ``one_mul``, ``add_mul``) follow by
  commutativity, so they are left to be proved rather than assumed.
- Subtraction, powers and the cast from N are *definitions*, so they cost
  no trust and compute:

      a - b  :=  a + -b
      a^n    :=  natrec((_)R, n, 1, (k, y) y ⋅ a)     a^(n+1) = a^n ⋅ a
      ↑n     :=  natrec((_)R, n, 0, (k, y) y + 1)     ↑(n+1)  = ↑n + 1

  recursing as Lean's ``Monoid.npow`` and ``Nat.cast`` do, so that a power
  or a literal imported from Lean means the same thing here.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from ..arity import A0, Arity, Arrow, cross
from ..binding import abstract, subst_many
from ..decl import SET, Operators, Param, Provenance, Registry, Signature, pvar
from ..render.notation import (
    ATOM,
    INFIX,
    NUMERAL,
    POWER,
    UNARY,
    notation,
)
from ..term import Abs, Const, Term, Var
from .identity import Id
from .nat import N, natrec, numeral

# precedences, as Lean's: = is 50 (library/identity.py)
ADDITIVE = 65
MULTIPLICATIVE = 70
UNARY_MINUS = 75
EXPONENT = 75

BINARY = Arrow(cross(A0, A0), A0)


@dataclass(frozen=True)
class CommRing:
    """The constants of one commutative ring; ``declare`` registers them.

    The ``Const`` objects are independent of any registry, as the library's
    other constants are, so a ring can be declared into several registries.
    """

    carrier: Const
    zero: Const
    one: Const
    add: Const
    mul: Const
    neg: Const
    sub: Const
    pow: Const
    cast: Const
    add_assoc: Const
    add_comm: Const
    add_zero: Const
    add_neg_cancel: Const
    mul_assoc: Const
    mul_comm: Const
    mul_one: Const
    mul_add: Const

    @property
    def laws(self) -> Tuple[Const, ...]:
        """The axioms, in the order of the module docstring."""
        return (
            self.add_assoc,
            self.add_comm,
            self.add_zero,
            self.add_neg_cancel,
            self.mul_assoc,
            self.mul_comm,
            self.mul_one,
            self.mul_add,
        )

    def literal(self, k: int) -> Term:
        """``0``, ``1``, or ``↑k`` for ``k >= 2``; negative ``k`` is negated."""
        if k < 0:
            return self.neg(self.literal(-k))
        if k == 0:
            return self.zero
        if k == 1:
            return self.one
        return self.cast(numeral(k))

    @property
    def operators(self) -> Operators:
        """The operator table that makes ``x + y`` mean ``add(x, y)``."""
        return Operators(
            self.carrier,
            self.add,
            self.mul,
            numeral=self.literal,
            neg=self.neg,
            sub=self.sub,
            pow=self.pow,
        )

    def declare(self, registry: Registry) -> None:
        """Add the carrier (unless already a set there), the operations, the
        definitions and the laws to ``registry``, and register the operators.
        """
        R = self.carrier
        if R not in registry:
            registry.declare(R, Signature((), SET))
        a, b, n = pvar("a"), pvar("b"), pvar("n")
        binary = Signature((Param(a, R), Param(b, R)), R)
        registry.declare(self.zero, Signature((), R))
        registry.declare(self.one, Signature((), R))
        registry.declare(self.add, binary)
        registry.declare(self.mul, binary)
        registry.declare(self.neg, Signature((Param(a, R),), R))

        x, y, k, m = Var("a"), Var("b"), Var("k"), Var("n")
        const_r = Abs((A0,), R, hints=("_",))
        registry.define(
            self.sub, abstract(self.add(x, self.neg(y)), [x, y]), binary
        )
        registry.define(
            self.pow,
            abstract(
                natrec(const_r, m, self.one, abstract(self.mul(y, x), [k, y])),
                [x, m],
            ),
            Signature((Param(a, R), Param(n, N)), R),
        )
        registry.define(
            self.cast,
            abstract(
                natrec(
                    const_r,
                    m,
                    self.zero,
                    abstract(self.add(y, self.one), [k, y]),
                ),
                [m],
            ),
            Signature((Param(n, N),), R),
        )

        for law, variables, lhs, rhs in self._statements():
            statement = Id(R, lhs, rhs)
            plain = {v: Var(v.name[1:]) for v in variables}
            registry.axiom(
                law,
                Signature(tuple(Param(v, R) for v in variables), statement),
                Provenance(
                    system="local",
                    name=law.name,
                    statement=subst_many(statement, plain).repr_unicode(),
                    note="commutative ring axiom (Mathlib: %s)"
                    % law.name.rsplit(".", 1)[-1],
                ),
            )
        registry.add_operators(self.operators)

    def _statements(
        self,
    ) -> Tuple[Tuple[Const, Tuple[Var, ...], Term, Term], ...]:
        """Each law as (constant, variables, lhs, rhs), over pattern vars."""
        a, b, c = pvar("a"), pvar("b"), pvar("c")
        add, mul = self.add, self.mul
        return (
            (self.add_assoc, (a, b, c), add(add(a, b), c), add(a, add(b, c))),
            (self.add_comm, (a, b), add(a, b), add(b, a)),
            (self.add_zero, (a,), add(a, self.zero), a),
            (self.add_neg_cancel, (a,), add(a, self.neg(a)), self.zero),
            (self.mul_assoc, (a, b, c), mul(mul(a, b), c), mul(a, mul(b, c))),
            (self.mul_comm, (a, b), mul(a, b), mul(b, a)),
            (self.mul_one, (a,), mul(a, self.one), a),
            (
                self.mul_add,
                (a, b, c),
                mul(a, add(b, c)),
                add(mul(a, b), mul(a, c)),
            ),
        )


def commutative_ring(carrier: Const, prefix: Optional[str] = None) -> CommRing:
    """The constants of a commutative ring on ``carrier``.

    They are named ``<prefix>.add``, ``<prefix>.add_comm`` and so on, the
    prefix defaulting to the carrier's name, and their notation is
    registered: ``+``, ``⋅``, ``-``, ``0``, ``1``, ``x²`` and literals. Nothing
    is declared until ``CommRing.declare``.
    """
    name = prefix or carrier.name

    def const(suffix: str, arity: Arity = A0) -> Const:
        return Const("%s.%s" % (name, suffix), arity)

    def law(suffix: str, variables: int) -> Const:
        return const(suffix, Arrow(cross(*[A0] * variables), A0))

    ring = CommRing(
        carrier=carrier,
        zero=const("zero"),
        one=const("one"),
        add=const("add", BINARY),
        mul=const("mul", BINARY),
        neg=const("neg", Arrow(A0, A0)),
        sub=const("sub", BINARY),
        pow=const("pow", BINARY),
        cast=const("cast", Arrow(A0, A0)),
        add_assoc=law("add_assoc", 3),
        add_comm=law("add_comm", 2),
        add_zero=law("add_zero", 1),
        add_neg_cancel=law("add_neg_cancel", 1),
        mul_assoc=law("mul_assoc", 3),
        mul_comm=law("mul_comm", 2),
        mul_one=law("mul_one", 1),
        mul_add=law("mul_add", 3),
    )

    def show(c: Const, kind: str, latex: str, unicode: str, **kw: int) -> None:
        notation(c, kind, latex=latex, unicode=unicode, typestring=c.name, **kw)

    show(ring.zero, ATOM, "0", "0")
    show(ring.one, ATOM, "1", "1")
    show(ring.add, INFIX, "+", "+", precedence=ADDITIVE)
    show(ring.sub, INFIX, "-", "-", precedence=ADDITIVE)
    show(ring.mul, INFIX, r"\cdot", "⋅", precedence=MULTIPLICATIVE)
    show(ring.neg, UNARY, "-", "-", precedence=UNARY_MINUS)
    show(ring.pow, POWER, "^", "^", precedence=EXPONENT)
    show(ring.cast, NUMERAL, r"{\uparrow}", "↑")
    return ring
