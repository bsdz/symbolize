"""Terms: the theory of expressions of [BN] ch. 3 as an immutable datatype.

A term is one of: a free variable, a bound variable (de Bruijn index), a
constant, an application, an abstraction, a combination or a selection. Every
term has an arity, computed and checked once at construction so that an
ill-kinded term cannot exist.

Binding is locally nameless: free variables are ``Var`` and bound variables are
``Bound`` indices, so alpha-equivalent terms are structurally equal and
substitution cannot capture. See ``binding.py`` for opening and closing
abstractions.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Iterator, List, Optional, Sequence, Tuple

from .arity import A0, Arity, Arrow, Cross, cross


class TermError(Exception):
    """Base class for errors raised when building or manipulating terms."""


class ArityError(TermError):
    """The arities of the parts of a term do not fit together."""


class Term:
    """Base class for all terms.

    Subclasses are frozen dataclasses; ``arity`` is populated in
    ``__post_init__`` and excluded from equality and hashing since it is a
    function of the other fields.
    """

    arity: Arity

    def __call__(self, *args: Term) -> "App":
        """``t(a, b)`` builds the application of ``t`` to ``a, b``."""
        return App(self, tuple(args))

    def __repr__(self) -> str:
        return _repr(self, [])

    # -- conveniences delegating to binding.py -------------------------------

    def abstract(self, *variables: "Var") -> "Abs":
        """``t.abstract(x, y)`` is ``(x, y)t``."""
        from .binding import abstract

        return abstract(self, variables)

    def subst(self, var: "Var", replacement: Term) -> Term:
        """``t.subst(x, a)`` is ``t[x := a]``."""
        from .binding import subst

        return subst(self, var, replacement)

    @property
    def free_vars(self) -> FrozenSet["Var"]:
        from .binding import free_vars

        return free_vars(self)

    def __contains__(self, var: object) -> bool:
        """``x in t``: does the free variable ``x`` occur in ``t``?"""
        return isinstance(var, Var) and var in self.free_vars


@dataclass(frozen=True, repr=False)
class Var(Term):
    """A free variable. Its type, if any, is given by a context."""

    name: str
    arity: Arity = A0


@dataclass(frozen=True, repr=False)
class Bound(Term):
    """A variable bound by an enclosing ``Abs``, as a de Bruijn index.

    Index ``i`` at depth ``d`` (the number of variables bound between the
    occurrence and the abstraction in question) refers to the ``(i - d)``-th
    variable of that abstraction.
    """

    index: int
    arity: Arity = A0

    def __post_init__(self) -> None:
        if self.index < 0:
            raise TermError("Bound index must be non-negative")


@dataclass(frozen=True, repr=False)
class Const(Term):
    """A constant. Its meaning, if any, is given by a registry."""

    name: str
    arity: Arity = A0


@dataclass(frozen=True, repr=False)
class App(Term):
    """Application ``fn(args...)`` [BN] 3.4.

    ``fn`` must have arity ``lhs -> rhs`` where ``lhs`` is the arity of the
    single argument, or the cross of the arities of several arguments.
    """

    fn: Term
    args: Tuple[Term, ...]
    arity: Arity = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        args = tuple(self.args)
        if len(args) == 1 and isinstance(args[0], Comb):
            args = args[0].items  # f((a, b)) is f(a, b)
        object.__setattr__(self, "args", args)
        if not self.args:
            raise ArityError("Application needs at least one argument")
        if not isinstance(self.fn.arity, Arrow):
            raise ArityError("Cannot apply a term of arity %r" % (self.fn.arity,))
        actual = cross(*[a.arity for a in self.args])
        if actual != self.fn.arity.lhs:
            raise ArityError(
                "Cannot apply: expected argument arity %r, got %r"
                % (self.fn.arity.lhs, actual)
            )
        object.__setattr__(self, "arity", self.fn.arity.rhs)


@dataclass(frozen=True, repr=False)
class Abs(Term):
    """Abstraction ``(x1, ..., xn)body`` [BN] 3.5.

    ``arities`` are the arities of the bound variables; ``hints`` are their
    display names and do not take part in equality.
    """

    arities: Tuple[Arity, ...]
    body: Term
    hints: Tuple[str, ...] = field(default=(), compare=False)
    arity: Arity = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arities", tuple(self.arities))
        if not self.arities:
            raise ArityError("Abstraction needs at least one variable")
        hints = tuple(self.hints) or tuple("x%d" % i for i in range(len(self.arities)))
        if len(hints) != len(self.arities):
            raise TermError("One display hint is needed per bound variable")
        object.__setattr__(self, "hints", hints)
        n = len(self.arities)
        for b, depth in bound_occurrences(self.body):
            i = b.index - depth
            if 0 <= i < n and b.arity != self.arities[i]:
                raise ArityError(
                    "Bound variable %d has arity %r but binder has %r"
                    % (i, b.arity, self.arities[i])
                )
        object.__setattr__(self, "arity", Arrow(cross(*self.arities), self.body.arity))


@dataclass(frozen=True, repr=False)
class Comb(Term):
    """Combination ``e1, ..., en`` (n >= 2) [BN] 3.6."""

    items: Tuple[Term, ...]
    arity: Arity = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        if len(self.items) < 2:
            raise ArityError("Combination needs at least two components")
        object.__setattr__(self, "arity", Cross(tuple(i.arity for i in self.items)))


@dataclass(frozen=True, repr=False)
class Sel(Term):
    """Selection ``(e).i`` of the ``i``-th component of a combination."""

    term: Term
    index: int
    arity: Arity = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.term.arity, Cross):
            raise ArityError(
                "Cannot select from a term of arity %r" % (self.term.arity,)
            )
        if not 0 <= self.index < len(self.term.arity.args):
            raise ArityError("Selection index %d out of range" % self.index)
        object.__setattr__(self, "arity", self.term.arity.args[self.index])


def children(term: Term) -> Tuple[Term, ...]:
    """The immediate subterms of ``term`` (empty for leaves)."""
    if isinstance(term, App):
        return (term.fn,) + term.args
    if isinstance(term, Abs):
        return (term.body,)
    if isinstance(term, Comb):
        return term.items
    if isinstance(term, Sel):
        return (term.term,)
    return ()


def bound_occurrences(term: Term, depth: int = 0) -> Iterator[Tuple[Bound, int]]:
    """Yield every ``Bound`` in ``term`` with the binding depth at which it
    occurs, where depth counts variables bound by abstractions inside
    ``term`` that enclose the occurrence."""
    if isinstance(term, Bound):
        yield term, depth
    elif isinstance(term, Abs):
        for b in bound_occurrences(term.body, depth + len(term.arities)):
            yield b
    else:
        for c in children(term):
            for b in bound_occurrences(c, depth):
                yield b


def is_closed(term: Term) -> bool:
    """True when no ``Bound`` in ``term`` escapes its abstractions, i.e. the
    term is locally closed and may be used at top level."""
    return all(b.index < depth for b, depth in bound_occurrences(term))


def _repr(term: Term, names: List[str]) -> str:
    """Debugging representation; ``names`` maps de Bruijn index to name."""
    if isinstance(term, Var):
        return term.name
    if isinstance(term, Const):
        return term.name
    if isinstance(term, Bound):
        if term.index < len(names):
            return names[term.index]
        return "#%d" % term.index
    if isinstance(term, App):
        return "%s(%s)" % (
            _repr_nested(term.fn, names),
            ", ".join(_repr(a, names) for a in term.args),
        )
    if isinstance(term, Abs):
        inner = _fresh_names(term.hints, names, _free_names(term.body))
        return "(%s)%s" % (
            ", ".join(inner),
            _repr_nested(term.body, list(inner) + names),
        )
    if isinstance(term, Comb):
        return ", ".join(_repr(i, names) for i in term.items)
    if isinstance(term, Sel):
        return "(%s).%d" % (_repr(term.term, names), term.index)
    raise TermError("Unknown term %r" % type(term))


def _free_names(term: Term) -> set:
    """Names of the free variables in ``term``."""
    if isinstance(term, Var):
        return {term.name}
    out: set = set()
    for c in children(term):
        out |= _free_names(c)
    return out


def _repr_nested(term: Term, names: List[str]) -> str:
    s = _repr(term, names)
    if isinstance(term, (Abs, Comb)):
        return "(" + s + ")"
    return s


def _fresh_names(
    hints: Sequence[str], taken: Sequence[str], avoid: Optional[set] = None
) -> Tuple[str, ...]:
    """Rename ``hints`` so they clash neither with ``taken`` nor with each
    other, by appending primes."""
    used = set(taken) | (avoid or set())
    out: List[str] = []
    for h in hints:
        name = h
        while name in used:
            name += "'"
        used.add(name)
        out.append(name)
    return tuple(out)
