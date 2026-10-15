"""R: a commutative ring standing in for the real numbers.

Only the ring axioms are declared so far (``library/ring.py``), so anything
proved about ``R`` holds in every commutative ring. The field and order
axioms come next. Even with them, ``R`` stays a postulated set rather than
a construction: symbolic algebra rewrites by algebraic laws and never needs
the elements, and constructive reals would bring undecidable equality.

The axioms are believed rather than proved, so ``R`` is not part of
``standard()``. Ask for it with ``standard(reals=True)`` or ``declare``.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..decl import Registry
from ..render.notation import ATOM, notation
from ..term import Const
from .ring import CommRing, commutative_ring

R = Const("R")
notation(R, ATOM, latex=r"\mathbb{R}", unicode="ℝ", typestring="R")

REAL: CommRing = commutative_ring(R)


def declare(registry: Registry) -> None:
    """Add ``R``, its operations and the ring axioms to ``registry``."""
    REAL.declare(registry)
