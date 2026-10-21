"""Id: the identity (equality) set ([BN] ch. 8, [ST] §5.3).

``Id(A, a, b)`` is the set of proofs that ``a`` and ``b`` are equal elements
of ``A``. Its only canonical inhabitant is ``refl(a) : Id(A, a, a)``, and its
eliminator ``J`` (``idpeel`` in [BN]) lets a family indexed by both endpoints
and by the proof be established from the reflexive case alone.

This is *propositional* equality, and is weaker than the definitional
equality decided by ``Evaluator.defeq``: ``plus(m, 0)`` and ``m`` are equal
definitionally only when the recursion can fire, whereas an inhabitant of
``Id(N, plus(m, 0), m)`` holds for a variable ``m`` as well -- but has to be
proved (or imported).

The derived rules ``symm``, ``trans``, ``cong`` and ``transport`` are
*definitions* over ``J`` (``declare``), so a proof built from them reads
``trans(p, q)`` rather than the ``J`` term it unfolds to, as Lean shows
``Eq.trans h₁ h₂``. They cost no trust and compute as ``J`` does. Their
leading arguments -- the set and the endpoints -- are implicit: shown in
the faithful typestring style, hidden in the pretty ones.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..binding import abstract
from ..decl import SET, Param, Registry, Rule, Signature, TypeFormer, pvar
from ..render.notation import EQUATION, PREFIX, notation
from ..term import Const, Var
from .pi import Pi, apply, lam

FAM3 = Arrow(Cross((A0, A0, A0)), A0)
FAM = Arrow(A0, A0)

Id = Const("Id", Arrow(Cross((A0, A0, A0)), A0))
refl = Const("refl", Arrow(A0, A0))
J = Const("J", Arrow(Cross((FAM3, A0, FAM)), A0))

# precedence 50, below every arithmetic operator, so x + y = y + x needs no
# parentheses; operators with no precedence are still parenthesised under it
notation(Id, EQUATION, latex="=", unicode="=", typestring="Id", precedence=50)
notation(refl, PREFIX)

_A, _a, _b, _c = pvar("A"), pvar("a"), pvar("b"), pvar("c")
_C, _d = pvar("C", FAM3), pvar("d", FAM)
_x, _y, _z = pvar("x"), pvar("y"), pvar("z")

IDENTITY = TypeFormer(
    former=Id,
    # A set    a ∈ A    b ∈ A
    # -------------------------
    #     Id(A, a, b) set
    formation=Signature((Param(_A, SET), Param(_a, _A), Param(_b, _A)), SET),
    #      a ∈ A
    # ---------------------
    # refl(a) ∈ Id(A, a, a)
    constructors=((refl, Signature((Param(_a, _A),), Id(_A, _a, _a))),),
    eliminators=(
        # C(x, y, z) set [x ∈ A, y ∈ A, z ∈ Id(A, x, y)]
        # c ∈ Id(A, a, b)    d(x) ∈ C(x, x, refl(x)) [x ∈ A]
        # ---------------------------------------------------
        #             J(C, c, d) ∈ C(a, b, c)
        (
            J,
            Signature(
                (
                    Param(
                        _C,
                        SET,
                        hyps=((_x, _A), (_y, _A), (_z, Id(_A, _x, _y))),
                    ),
                    Param(_c, Id(_A, _a, _b)),
                    Param(_d, _C(_x, _x, refl(_x)), hyps=((_x, _A),)),
                ),
                _C(_a, _b, _c),
            ),
        ),
    ),
    # J(C, refl(a), d) = d(a)
    computation=(Rule(J(_C, refl(_a), _d), _d(_a)),),
)


# -- derived rules, as definitions over J --------------------------------------

symm = Const("symm", Arrow(Cross((A0,) * 4), A0))
trans = Const("trans", Arrow(Cross((A0,) * 6), A0))
cong = Const("cong", Arrow(Cross((A0, A0, A0, A0, FAM, A0)), A0))
transport = Const("transport", Arrow(Cross((A0, FAM, A0, A0, A0, A0)), A0))

# the context of cong and the motive of transport precede the proofs, after
# the implicit arguments, so cong shows as cong((t)t + 1, h)
notation(symm, PREFIX, implicit=3)
notation(trans, PREFIX, implicit=4)
notation(cong, PREFIX, implicit=4)
notation(transport, PREFIX, implicit=4)

_B, _p, _q = pvar("B"), pvar("p"), pvar("q")
_P = pvar("P", FAM)


def _derived() -> tuple:
    """Each derived rule as (constant, signature, body).

    The bodies are the J terms derive.py used to build inline: plain
    variables, bound at once, whose names survive only as display hints.
    """
    A, B, a, b, c = Var("A"), Var("B"), Var("a"), Var("b"), Var("c")
    p, q = Var("p"), Var("q")
    x, y, z, w = Var("x"), Var("y"), Var("z"), Var("w")
    C, P = Var("C", FAM), Var("P", FAM)
    identity = lam(abstract(w, [w]))

    #  symm(p) : b = a       J((x, y, z) y = x, p, (x) refl(x))
    symm_body = abstract(
        J(abstract(Id(A, y, x), [x, y, z]), p, abstract(refl(x), [x])),
        [A, a, b, p],
    )
    #  trans(p, q) : a = c   J((x, y, z) a = x ⇒ a = y, q, (x) λw.w)(p)
    trans_body = abstract(
        apply(
            J(
                abstract(
                    Pi(Id(A, a, x), abstract(Id(A, a, y), [w])), [x, y, z]
                ),
                q,
                abstract(identity, [x]),
            ),
            p,
        ),
        [A, a, b, c, p, q],
    )
    #  cong(C, p) : C(a) = C(b)     J((x, y, z) C(x) = C(y), p, (x) refl(C(x)))
    cong_body = abstract(
        J(
            abstract(Id(B, C(x), C(y)), [x, y, z]),
            p,
            abstract(refl(C(x)), [x]),
        ),
        [A, B, a, b, C, p],
    )
    #  transport(p, c) : P(b)       J((x, y, z) P(x) ⇒ P(y), p, (x) λw.w)(c)
    transport_body = abstract(
        apply(
            J(
                abstract(Pi(P(x), abstract(P(y), [w])), [x, y, z]),
                p,
                abstract(identity, [x]),
            ),
            c,
        ),
        [A, P, a, b, p, c],
    )

    return (
        (
            symm,
            Signature(
                (
                    Param(_A, SET),
                    Param(_a, _A),
                    Param(_b, _A),
                    Param(_p, Id(_A, _a, _b)),
                ),
                Id(_A, _b, _a),
            ),
            symm_body,
        ),
        (
            trans,
            Signature(
                (
                    Param(_A, SET),
                    Param(_a, _A),
                    Param(_b, _A),
                    Param(_c, _A),
                    Param(_p, Id(_A, _a, _b)),
                    Param(_q, Id(_A, _b, _c)),
                ),
                Id(_A, _a, _c),
            ),
            trans_body,
        ),
        (
            cong,
            Signature(
                (
                    Param(_A, SET),
                    Param(_B, SET),
                    Param(_a, _A),
                    Param(_b, _A),
                    Param(_d, _B, hyps=((_x, _A),)),
                    Param(_p, Id(_A, _a, _b)),
                ),
                Id(_B, _d(_a), _d(_b)),
            ),
            cong_body,
        ),
        (
            transport,
            Signature(
                (
                    Param(_A, SET),
                    Param(_P, SET, hyps=((_x, _A),)),
                    Param(_a, _A),
                    Param(_b, _A),
                    Param(_p, Id(_A, _a, _b)),
                    Param(_c, _P(_a)),
                ),
                _P(_b),
            ),
            transport_body,
        ),
    )


DERIVED = tuple(const for const, _, _ in _derived())


def declare(registry: Registry) -> None:
    """Add the derived rules to ``registry`` (the former is added
    separately), each with a signature so that a proof using one is checked
    without unfolding it."""
    for const, signature, body in _derived():
        registry.define(const, body, signature)
