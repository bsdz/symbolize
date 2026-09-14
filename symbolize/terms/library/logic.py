"""The logical connectives as abbreviations ([ST] ch. 4):

    A ⇒ B  :=  Π(A, (_)B)        ∀(A, B)  :=  Π(A, B)
    A ∧ B  :=  Σ(A, (_)B)        ∃(A, B)  :=  Σ(A, B)
    A ∨ B  :=  A + B             ¬A       :=  A ⇒ ⊥

Renderers show the connective; the evaluator unfolds it on demand.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..arity import A0, Arrow, Cross
from ..binding import abstract
from ..decl import SET, Param, Registry, Signature, pvar
from ..term import Abs, Const
from .falsum import Falsum
from .pi import Pi
from .plus import Plus
from .sigma import Sigma

FAM = Arrow(A0, A0)

implies = Const("⟹", Arrow(Cross((A0, A0)), A0))
and_ = Const("∧", Arrow(Cross((A0, A0)), A0))
or_ = Const("∨", Arrow(Cross((A0, A0)), A0))
not_ = Const("¬", Arrow(A0, A0))
forall = Const("∀", Arrow(Cross((A0, FAM)), A0))
exists = Const("∃", Arrow(Cross((A0, FAM)), A0))

_A, _B, _x = pvar("A"), pvar("B"), pvar("x")
_F = pvar("F", FAM)


def _const_family(body):
    return Abs((A0,), body, hints=("_",))


_binary = Signature((Param(_A, SET), Param(_B, SET)), SET)
_quantifier = Signature((Param(_A, SET), Param(_F, SET, hyps=((_x, _A),))), SET)


def declare(registry: Registry) -> None:
    """Add the connectives to ``registry``."""
    registry.define(implies, abstract(Pi(_A, _const_family(_B)), [_A, _B]), _binary)
    registry.define(and_, abstract(Sigma(_A, _const_family(_B)), [_A, _B]), _binary)
    registry.define(or_, abstract(Plus(_A, _B), [_A, _B]), _binary)
    registry.define(
        not_,
        abstract(Pi(_A, _const_family(Falsum)), [_A]),
        Signature((Param(_A, SET),), SET),
    )
    registry.define(forall, abstract(Pi(_A, _F), [_A, _F]), _quantifier)
    registry.define(exists, abstract(Sigma(_A, _F), [_A, _F]), _quantifier)
