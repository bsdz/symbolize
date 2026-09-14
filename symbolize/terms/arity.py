"""Arities: the kinds of expressions in the theory of expressions [BN] ch. 3.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


class Arity:
    """Base class for arities. Instances are immutable and hashable."""

    def _repr_nested(self) -> str:
        """Representation when nested inside another arity."""
        return "(" + repr(self) + ")"


@dataclass(frozen=True)
class Zero(Arity):
    """The arity of saturated expressions, written ``0`` in [BN]."""

    def __repr__(self) -> str:
        return "0"

    def _repr_nested(self) -> str:
        return repr(self)


@dataclass(frozen=True)
class Arrow(Arity):
    """The arity ``lhs -> rhs`` of expressions that can be applied."""

    lhs: Arity
    rhs: Arity

    def __repr__(self) -> str:
        return "%s ⟶ %s" % (self.lhs._repr_nested(), self.rhs._repr_nested())


@dataclass(frozen=True)
class Cross(Arity):
    """The arity ``a1 ⊗ ... ⊗ an`` (n >= 2) of combinations."""

    args: Tuple[Arity, ...]

    def __post_init__(self) -> None:
        if len(self.args) < 2:
            raise ValueError("Cross arity needs at least two components")

    def __repr__(self) -> str:
        return " ⊗ ".join(a._repr_nested() for a in self.args)


A0 = Zero()


def cross(*arities: Arity) -> Arity:
    """Build a ``Cross`` arity, collapsing the one-component case.

    Args:
        arities: component arities, at least one.

    Returns:
        the single arity when one is given, otherwise a ``Cross``.
    """
    if not arities:
        raise ValueError("cross needs at least one arity")
    if len(arities) == 1:
        return arities[0]
    return Cross(tuple(arities))


def arrow(lhs: Arity, *rest: Arity) -> Arity:
    """Build a right-nested ``Arrow`` chain ``a1 -> (a2 -> (... -> an))``.

    Args:
        lhs: first arity.
        rest: remaining arities; the last is the final result arity.

    Returns:
        ``lhs`` itself when ``rest`` is empty.
    """
    if not rest:
        return lhs
    return Arrow(lhs, arrow(*rest))
