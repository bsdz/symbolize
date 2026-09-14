"""The evaluator: weak head normal form, normal form and definitional
equality, driven lazily and bounded by a step budget.

Reductions:

* beta:      ``((x)b)(a)  ->  b[x := a]``
* selection: ``(a, b).1   ->  b``
* delta:     unfold a defined constant (``Registry.definition``)
* iota:      fire a computation rule (``Registry.rules``)

Eta for abstractions and combinations is handled in ``defeq`` rather than
by rewriting. Nothing is evaluated at construction; call ``whnf``/``nf``.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

from .arity import Arrow, Cross
from .binding import abstract, free_vars, instantiate, open_abs
from .decl import Registry
from .term import Abs, App, Comb, Const, Sel, Term, TermError, Var

DEFAULT_FUEL = 10_000


class ReductionLimit(TermError):
    """The step budget was exhausted; the term may not have a normal form."""


class Evaluator:
    """Reduces terms with respect to a registry within a step budget.

    An evaluator caches weak head normal forms for its lifetime; make a new
    one when the registry changes.
    """

    def __init__(self, registry: Optional[Registry] = None, fuel: int = DEFAULT_FUEL):
        self.registry = registry if registry is not None else Registry()
        self.fuel = fuel
        self._steps = 0
        self._whnf_cache: Dict[Term, Term] = {}

    # -- bookkeeping ---------------------------------------------------------

    @property
    def steps(self) -> int:
        """Reduction steps taken so far."""
        return self._steps

    def _step(self) -> None:
        self._steps += 1
        if self._steps > self.fuel:
            raise ReductionLimit("Reduction did not finish within %d steps" % self.fuel)

    # -- weak head normal form ------------------------------------------------

    def whnf(self, term: Term) -> Term:
        """Reduce the head of ``term`` until it is a variable, a constant
        without an applicable definition or rule, an abstraction, a
        combination, or a stuck application/selection."""
        original = term
        seen = []
        while True:
            cached = self._whnf_cache.get(term)
            if cached is not None:
                term = cached
                break
            seen.append(term)
            reduced = self._head_step(term)
            if reduced is None or reduced == term:
                break
            self._step()
            term = reduced
        for t in seen:
            self._whnf_cache[t] = term
        self._whnf_cache[original] = term
        return term

    def _head_step(self, term: Term) -> Optional[Term]:
        """One head reduction step, or None when ``term`` is in whnf."""
        if isinstance(term, Const):
            definition = self.registry.definition(term)
            return definition.body if definition is not None else None

        if isinstance(term, Sel):
            inner = self.whnf(term.term)
            if isinstance(inner, Comb):
                return inner.items[term.index]
            return Sel(inner, term.index)

        if isinstance(term, App):
            fn = self.whnf(term.fn)
            if isinstance(fn, Abs):
                return beta(fn, term.args)
            if isinstance(fn, Const):
                definition = self.registry.definition(fn)
                if definition is not None:
                    return App(definition.body, term.args)
                if self.registry.rules(fn):
                    return self._iota(fn, term.args)
            return App(fn, term.args)

        return None

    def _iota(self, head: Const, args: Tuple[Term, ...]) -> Term:
        """Try the computation rules for ``head``. The major arguments are
        reduced first so constructor forms become visible; if no rule fires
        the application with those reduced arguments is the stuck form."""
        reduced = list(args)
        for i in self.registry.major(head):
            if i < len(reduced):
                reduced[i] = self.whnf(reduced[i])
        candidate = App(head, tuple(reduced))
        for rule in self.registry.rules(head):
            bindings = rule.match(candidate)
            if bindings is not None:
                return rule.fire(bindings)
        return candidate

    # -- normal form ----------------------------------------------------------

    def nf(self, term: Term) -> Term:
        """Fully normalise ``term``.

        Abstractions are opened with fresh variables before their bodies are
        normalised, so reduction never happens under a dangling index.
        """
        self._step()  # visiting counts, so cyclic unfoldings hit the budget
        term = self.whnf(term)
        if isinstance(term, App):
            return App(self.nf(term.fn), tuple(self.nf(a) for a in term.args))
        if isinstance(term, Abs):
            variables, body = open_abs(term)
            return abstract(self.nf(body), variables, term.hints)
        if isinstance(term, Comb):
            return Comb(tuple(self.nf(i) for i in term.items))
        if isinstance(term, Sel):
            return Sel(self.nf(term.term), term.index)
        return term

    # -- definitional equality ------------------------------------------------

    def defeq(self, a: Term, b: Term) -> bool:
        """Decide ``a = b`` up to beta, delta, iota, selection and eta."""
        if a == b:
            return True
        if a.arity != b.arity:
            return False
        a = self.whnf(a)
        b = self.whnf(b)
        if a == b:
            return True

        if isinstance(a, Abs) or isinstance(b, Abs):
            return self._defeq_functions(a, b)
        if isinstance(a, Comb) or isinstance(b, Comb):
            return self._defeq_combinations(a, b)
        if isinstance(a, App) and isinstance(b, App):
            return (
                len(a.args) == len(b.args)
                and self.defeq(a.fn, b.fn)
                and all(self.defeq(x, y) for x, y in zip(a.args, b.args))
            )
        if isinstance(a, Sel) and isinstance(b, Sel):
            return a.index == b.index and self.defeq(a.term, b.term)
        return False

    def _defeq_functions(self, a: Term, b: Term) -> bool:
        """Compare under a binder; eta-expand the side that is not an
        abstraction."""
        assert isinstance(a.arity, Arrow)
        template = a if isinstance(a, Abs) else b
        assert isinstance(template, Abs)
        avoid = {v.name for v in free_vars(a) | free_vars(b)}
        variables, _ = open_abs(template, avoid)
        return self.defeq(_apply_to(a, variables), _apply_to(b, variables))

    def _defeq_combinations(self, a: Term, b: Term) -> bool:
        """Compare componentwise; select from the side that is not a
        combination (surjective pairing)."""
        assert isinstance(a.arity, Cross)
        n = len(a.arity.args)
        return all(self.defeq(_component(a, i), _component(b, i)) for i in range(n))


def beta(fn: Abs, args: Sequence[Term]) -> Term:
    """Beta-reduce ``fn(args)``, adapting between a binder of several
    variables and a single argument of cross arity (and vice versa)."""
    args = tuple(args)
    n = len(fn.arities)
    if len(args) == n:
        return instantiate(fn, args)
    if len(args) == 1:  # (x, y)b applied to p : 0 ⊗ 0
        return instantiate(fn, tuple(Sel(args[0], i) for i in range(n)))
    if n == 1:  # (p)b applied to a, b
        return instantiate(fn, (Comb(args),))
    raise TermError("beta: cannot fit %d arguments to %d binders" % (len(args), n))


def _apply_to(term: Term, variables: Tuple[Var, ...]) -> Term:
    if isinstance(term, Abs):
        return instantiate(term, variables)
    return App(term, variables)


def _component(term: Term, i: int) -> Term:
    if isinstance(term, Comb):
        return term.items[i]
    return Sel(term, i)


# -- module-level conveniences ---------------------------------------------------


def whnf(
    term: Term, registry: Optional[Registry] = None, fuel: int = DEFAULT_FUEL
) -> Term:
    return Evaluator(registry, fuel).whnf(term)


def nf(
    term: Term, registry: Optional[Registry] = None, fuel: int = DEFAULT_FUEL
) -> Term:
    return Evaluator(registry, fuel).nf(term)


def defeq(
    a: Term, b: Term, registry: Optional[Registry] = None, fuel: int = DEFAULT_FUEL
) -> bool:
    return Evaluator(registry, fuel).defeq(a, b)
