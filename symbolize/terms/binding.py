"""Locally-nameless binding operations: closing and opening abstractions,
substitution for free variables, free-variable queries.

All functions take and return locally closed terms (no escaping ``Bound``)
except where noted; ``abstract`` closes over free variables to build an
``Abs`` and ``instantiate`` opens one.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from typing import (Callable, Dict, FrozenSet, Iterable, Optional, Sequence,
                    Tuple)

from .term import (Abs, App, ArityError, Bound, Comb, Sel, Term, TermError,
                   Var, _fresh_names, children)

Transform = Callable[[Term, int], Optional[Term]]


def transform(term: Term, fn: Transform, depth: int = 0) -> Term:
    """Rebuild ``term`` bottom-up, letting ``fn`` replace subterms.

    ``fn(subterm, depth)`` returns a replacement, or ``None`` to recurse
    into the subterm's children instead. ``depth`` counts the variables
    bound by abstractions between ``term`` and the subterm.
    """
    replacement = fn(term, depth)
    if replacement is not None:
        return replacement
    if isinstance(term, App):
        return App(
            transform(term.fn, fn, depth),
            tuple(transform(a, fn, depth) for a in term.args),
        )
    if isinstance(term, Abs):
        inner = depth + len(term.arities)
        return Abs(term.arities, transform(term.body, fn, inner), term.hints)
    if isinstance(term, Comb):
        return Comb(tuple(transform(i, fn, depth) for i in term.items))
    if isinstance(term, Sel):
        return Sel(transform(term.term, fn, depth), term.index)
    return term


def free_vars(term: Term) -> FrozenSet[Var]:
    """The free variables occurring in ``term``."""
    if isinstance(term, Var):
        return frozenset([term])
    result: FrozenSet[Var] = frozenset()
    for c in children(term):
        result |= free_vars(c)
    return result


def contains_free(term: Term, var: Var) -> bool:
    """True when ``var`` occurs (necessarily free) in ``term``."""
    return var in free_vars(term)


def abstract(
    term: Term, variables: Sequence[Var], hints: Optional[Sequence[str]] = None
) -> Abs:
    """Close ``term`` over ``variables`` to build ``(x1, ..., xn)term``.

    Occurrences of ``variables[j]`` become bound to the ``j``-th binder;
    display hints default to the variables' names.
    """
    variables = tuple(variables)
    if not variables:
        raise TermError("abstract needs at least one variable")
    if len(set(variables)) != len(variables):
        raise TermError("abstract: variables must be distinct")
    positions: Dict[Var, int] = {v: j for j, v in enumerate(variables)}

    def close(t: Term, depth: int) -> Optional[Term]:
        if isinstance(t, Var) and t in positions:
            return Bound(depth + positions[t], t.arity)
        return None

    return Abs(
        tuple(v.arity for v in variables),
        transform(term, close),
        tuple(hints) if hints is not None else tuple(v.name for v in variables),
    )


def instantiate(abstraction: Abs, args: Sequence[Term]) -> Term:
    """Open ``abstraction`` by replacing its bound variables with ``args``.

    ``args`` must be locally closed and match the binder arities.
    """
    args = tuple(args)
    n = len(abstraction.arities)
    if len(args) != n:
        raise ArityError("instantiate: expected %d arguments, got %d" % (n, len(args)))
    for a, expected in zip(args, abstraction.arities):
        if a.arity != expected:
            raise ArityError(
                "instantiate: expected arity %r, got %r" % (expected, a.arity)
            )

    def open_(t: Term, depth: int) -> Optional[Term]:
        if isinstance(t, Bound):
            i = t.index - depth
            if 0 <= i < n:
                return args[i]
            if i >= n:  # bound further out: the binder in between is gone
                return Bound(t.index - n, t.arity)
        return None

    return transform(abstraction.body, open_)


def open_abs(
    abstraction: Abs, avoid: Iterable[str] = ()
) -> Tuple[Tuple[Var, ...], Term]:
    """Open ``abstraction`` with fresh free variables named after its hints.

    Names avoid the free variables of the body and any in ``avoid``.
    """
    taken = {v.name for v in free_vars(abstraction.body)} | set(avoid)
    names = _fresh_names(abstraction.hints, (), taken)
    variables = tuple(Var(nm, a) for nm, a in zip(names, abstraction.arities))
    return variables, instantiate(abstraction, variables)


def subst(term: Term, var: Var, replacement: Term) -> Term:
    """Replace every occurrence of the free variable ``var`` in ``term`` by
    the locally closed ``replacement``. Capture is impossible: bound
    variables are indices, not names."""
    return subst_many(term, {var: replacement})


def subst_many(term: Term, mapping: Dict[Var, Term]) -> Term:
    """Simultaneously replace free variables per ``mapping``."""
    for var, replacement in mapping.items():
        if replacement.arity != var.arity:
            raise ArityError(
                "subst: %r has arity %r but replacement has %r"
                % (var, var.arity, replacement.arity)
            )

    def replace(t: Term, depth: int) -> Optional[Term]:
        if isinstance(t, Var) and t in mapping:
            return mapping[t]
        return None

    return transform(term, replace)
