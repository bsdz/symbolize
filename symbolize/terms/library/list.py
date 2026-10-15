"""List: finite lists ([BN] ch. 16, [ST] §4.8).

    A set                          a ∈ A    as ∈ List(A)
    --------------      -------    ---------------------
    List(A) set         nil        cons(a, as) ∈ List(A)

The eliminator is primitive recursion over the list, ``listrec``, which the
legacy ``definitions/misc.py`` provided as a bare symbol with no rules.

Polymorphic *functions* over lists -- ``length``, ``append`` -- are not
declared here. Without universes there is no implicit argument, so each
would have to take its element set explicitly (``length(A, xs)``), and that
convention is better settled when universes arrive (roadmap step 5). The
eliminator itself is enough to define them at a concrete set in the
meantime.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..decl import SET, Param, Rule, Signature, TypeFormer, pvar
from ..render.notation import ATOM, INFIX, notation
from ..term import Const, Term

FAM = Arrow(A0, A0)
STEP3 = Arrow(Cross((A0, A0, A0)), A0)

List = Const("List", Arrow(A0, A0))
nil = Const("nil")
cons = Const("cons", Arrow(Cross((A0, A0)), A0))
listrec = Const("listrec", Arrow(Cross((FAM, A0, A0, STEP3)), A0))

notation(List, ATOM, latex=r"\mathrm{List}", unicode="List", typestring="List")
notation(nil, ATOM, latex=r"[\,]", unicode="[]", typestring="nil")
notation(cons, INFIX, latex=r"\mathbin{::}", unicode="∷", typestring="cons")

_A, _C = pvar("A"), pvar("C", FAM)
_a, _as, _l, _c, _e = (
    pvar("a"),
    pvar("as"),
    pvar("l"),
    pvar("c"),
    pvar("e", STEP3),
)
_x, _xs, _y, _z = pvar("x"), pvar("xs"), pvar("y"), pvar("z")

LIST = TypeFormer(
    former=List,
    formation=Signature((Param(_A, SET),), SET),
    constructors=(
        (nil, Signature((), List(_A))),
        (
            cons,
            Signature(
                (Param(_a, _A), Param(_as, List(_A))),
                List(_A),
            ),
        ),
    ),
    # C(z) set [z ∈ List(A)]   l ∈ List(A)   c ∈ C(nil)
    # e(x, xs, y) ∈ C(cons(x, xs)) [x ∈ A, xs ∈ List(A), y ∈ C(xs)]
    # -------------------------------------------------------------
    #               listrec(C, l, c, e) ∈ C(l)
    eliminators=(
        (
            listrec,
            Signature(
                (
                    Param(_C, SET, hyps=((_z, List(_A)),)),
                    Param(_l, List(_A)),
                    Param(_c, _C(nil)),
                    Param(
                        _e,
                        _C(cons(_x, _xs)),
                        hyps=((_x, _A), (_xs, List(_A)), (_y, _C(_xs))),
                    ),
                ),
                _C(_l),
            ),
        ),
    ),
    computation=(
        Rule(listrec(_C, nil, _c, _e), _c),
        Rule(
            listrec(_C, cons(_a, _as), _c, _e),
            _e(_a, _as, listrec(_C, _as, _c, _e)),
        ),
    ),
)


def listing(*items: Term) -> Term:
    """``cons(a, cons(b, ... nil))`` for the given items, in order.

    The list analogue of ``nat.numeral``: ``listing()`` is ``nil``.
    """
    out: Term = nil
    for item in reversed(items):
        out = cons(item, out)
    return out
