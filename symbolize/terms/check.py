"""The type checker: judgements ``a ∈ A`` and ``A set`` under hypotheses,
decided bidirectionally against the signatures in a registry.

Only terms of arity ``0`` have types. Higher-arity variables (families,
hypothetical premises) live in the context as ``Param`` entries, e.g.
``C(z) set [z ∈ N]``. Equality of types is definitional (``Evaluator.defeq``).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, List, Optional, Sequence, Tuple

from .arity import A0
from .binding import free_vars, instantiate, subst_many, transform
from .decl import SET, Param, Registry, Signature, match
from .eval import Evaluator, beta
from .term import Abs, App, Const, Term, TermError, Var, _fresh_names, is_closed


class TypingError(TermError):
    """A term does not have the required type, or cannot be typed."""


class _NeedsExpected(Exception):
    """Internal: a premise could not be inferred; retry once more pattern
    variables are known, or report ``error`` if none become known."""

    def __init__(self, error: TypingError):
        super().__init__(str(error))
        self.error = error


class Context:
    """Hypotheses ``x ∈ A`` (and hypothetical ones for families), ordered.

    Immutable: ``extend`` returns a new context.
    """

    def __init__(self, entries: Iterable[Param] = ()):
        self._entries: Tuple[Param, ...] = tuple(entries)
        self._index: Dict[Var, Param] = {p.var: p for p in self._entries}

    def extend(self, var: Var, type: Term, hyps: Sequence[Tuple[Var, Term]] = ()):
        """A new context with ``var ∈ type`` (hypothetically, if ``hyps``)."""
        if var in self._index:
            raise TypingError("%r is already in the context" % (var,))
        return Context(self._entries + (Param(var, type, tuple(hyps)),))

    def lookup(self, var: Var) -> Optional[Param]:
        return self._index.get(var)

    @property
    def entries(self) -> Tuple[Param, ...]:
        return self._entries

    @property
    def vars(self) -> Tuple[Var, ...]:
        return tuple(p.var for p in self._entries)

    def names(self) -> FrozenSet[str]:
        return frozenset(v.name for v in self.vars)

    def __contains__(self, var: object) -> bool:
        return var in self._index

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Context) and self._entries == other._entries

    def __hash__(self) -> int:
        return hash(self._entries)

    def __repr__(self) -> str:
        return "[%s]" % ", ".join(_repr_param(p) for p in self._entries)


def _repr_param(p: Param) -> str:
    if not p.hyps:
        return "%s ∈ %s" % (p.var, p.type)
    args = ", ".join(x.name for x, _ in p.hyps)
    hyps = ", ".join("%s ∈ %s" % (x, a) for x, a in p.hyps)
    return "%s(%s) ∈ %s [%s]" % (p.var, args, p.type, hyps)


EMPTY = Context()


class Checker:
    """Infers and checks types with respect to a registry."""

    def __init__(self, registry: Registry, evaluator: Optional[Evaluator] = None):
        self.registry = registry
        self.evaluator = evaluator if evaluator is not None else Evaluator(registry)

    # -- public ----------------------------------------------------------------

    def infer(self, ctx: Context, term: Term) -> Term:
        """The type of ``term`` in ``ctx``; raises ``TypingError``."""
        if term.arity != A0:
            raise TypingError("Only saturated terms have types: %r" % (term,))
        if term == SET:
            raise TypingError("Set has no type (there are no universes)")

        if isinstance(term, Var):
            entry = ctx.lookup(term)
            if entry is None:
                raise TypingError("Variable %r is not in the context" % (term,))
            assert entry.type is not None
            return entry.type

        if isinstance(term, Const):
            return self._infer_const(ctx, term, ())

        if isinstance(term, App):
            fn = term.fn
            if isinstance(fn, Const):
                return self._infer_const(ctx, fn, term.args)
            if isinstance(fn, Var):
                return self._infer_family(ctx, fn, term.args)
            if isinstance(fn, Abs):
                return self.infer(ctx, beta(fn, term.args))
            head = self.evaluator.whnf(term)
            if head != term:
                return self.infer(ctx, head)
            raise TypingError("Cannot type application %r" % (term,))

        raise TypingError("Cannot infer a type for %r" % (term,))

    def check(self, ctx: Context, term: Term, type: Term) -> None:
        """Verify ``term ∈ type`` in ``ctx``; raises ``TypingError``."""
        if isinstance(term, App) and isinstance(term.fn, Const):
            signature = self.registry.signature(term.fn)
            if signature is not None:
                actual = self._apply_signature(ctx, signature, term.args, type)
                self._expect(ctx, term, actual, type)
                return
        actual = self.infer(ctx, term)
        self._expect(ctx, term, actual, type)

    def is_set(self, ctx: Context, term: Term) -> None:
        """Verify the judgement ``term set``."""
        self.check(ctx, term, SET)

    def defeq(self, a: Term, b: Term) -> bool:
        return self.evaluator.defeq(a, b)

    # -- constants ---------------------------------------------------------------

    def _infer_const(self, ctx: Context, const: Const, args: Tuple[Term, ...]) -> Term:
        signature = self.registry.signature(const)
        if signature is not None:
            return self._apply_signature(ctx, signature, args, None)
        definition = self.registry.definition(const)
        if definition is not None:
            body = definition.body
            return self.infer(ctx, App(body, args) if args else body)
        raise TypingError("Constant %r is not declared" % (const,))

    def _infer_family(self, ctx: Context, var: Var, args: Tuple[Term, ...]) -> Term:
        entry = ctx.lookup(var)
        if entry is None:
            raise TypingError("Variable %r is not in the context" % (var,))
        if len(entry.hyps) != len(args):
            raise TypingError(
                "%r expects %d arguments, got %d" % (var, len(entry.hyps), len(args))
            )
        bindings: Dict[Var, Term] = {}
        for (x, a), arg in zip(entry.hyps, args):
            self.check(ctx, arg, _instantiate(a, bindings))
            bindings[x] = arg
        assert entry.type is not None
        return _instantiate(entry.type, bindings)

    # -- signatures --------------------------------------------------------------

    def _apply_signature(
        self,
        ctx: Context,
        signature: Signature,
        args: Tuple[Term, ...],
        expected: Optional[Term],
    ) -> Term:
        """Type ``c(args)`` by its signature, binding pattern variables from
        the arguments (and from ``expected`` when checking)."""
        if len(args) != len(signature.params):
            raise TypingError(
                "Expected %d arguments, got %d" % (len(signature.params), len(args))
            )
        pattern_vars = signature.vars
        bindings: Dict[Var, Term] = {}

        if expected is not None and _rigid(signature.result, pattern_vars):
            # checking mode: learn what we can from the expected type
            match(
                signature.result,
                self.evaluator.whnf(expected),
                pattern_vars,
                bindings,
                eq=self.defeq,
            )

        pending: List[Tuple[Param, Term]] = list(zip(signature.params, args))
        deferred: Optional[TypingError] = None
        while pending:
            progress = False
            for item in list(pending):
                param, arg = item
                try:
                    done = self._try_premise(ctx, param, arg, pattern_vars, bindings)
                except _NeedsExpected as e:
                    # the argument cannot be inferred on its own; another
                    # premise may still fix the pattern variables it needs
                    deferred = deferred or e.error
                    done = False
                if done:
                    pending.remove(item)
                    progress = True
            if not progress:
                if deferred is not None:
                    raise deferred
                unbound = sorted(
                    v.name for p, _ in pending for v in _needed(p) - set(bindings)
                )
                raise TypingError(
                    "Cannot determine %s; an expected type is needed"
                    % ", ".join(unbound)
                )

        result = _instantiate(signature.result, bindings)
        left = free_vars(result) & pattern_vars
        if left:
            raise TypingError(
                "Cannot determine %s in the result type; an expected type is needed"
                % ", ".join(sorted(v.name for v in left))
            )
        return result

    def _try_premise(
        self,
        ctx: Context,
        param: Param,
        arg: Term,
        pattern_vars: FrozenSet[Var],
        bindings: Dict[Var, Term],
    ) -> bool:
        """Discharge one premise if enough pattern variables are known.
        Returns False to defer it."""
        needed = _needed(param)
        unbound = needed - set(bindings)

        if param.type is None:  # kind-only argument (nothing to check)
            bindings[param.var] = arg
            return True

        if param.hyps:
            if unbound:
                return False
            self._check_hypothetical(ctx, param, arg, bindings)
            bindings[param.var] = arg
            return True

        if not unbound:
            self.check(ctx, arg, _instantiate(param.type, bindings))
            bindings[param.var] = arg
            return True

        # infer the argument's type and match it against the schema
        if arg.arity != A0:
            return False
        try:
            inferred = self.evaluator.whnf(self.infer(ctx, arg))
        except TypingError as e:
            raise _NeedsExpected(e)
        if not match(param.type, inferred, pattern_vars, bindings, eq=self.defeq):
            raise TypingError(
                "%r has type %r, which does not fit %r"
                % (arg, inferred, _instantiate(param.type, bindings))
            )
        bindings[param.var] = arg
        return True

    def _check_hypothetical(
        self, ctx: Context, param: Param, arg: Term, bindings: Dict[Var, Term]
    ) -> None:
        """``arg(x1..xk) ∈ T [x1 ∈ A1, ..., xk ∈ Ak]``: open with fresh
        variables and check the body in the extended context."""
        assert param.type is not None
        local = dict(bindings)
        avoid = set(ctx.names()) | {v.name for v in free_vars(arg)}
        for _, a in param.hyps:
            avoid |= {v.name for v in free_vars(a)}
        names = _fresh_names([x.name.lstrip("?") for x, _ in param.hyps], (), avoid)
        fresh: List[Var] = []
        inner = ctx
        for (x, a), name in zip(param.hyps, names):
            v = Var(name, x.arity)
            inner = inner.extend(v, _instantiate(a, local))
            local[x] = v
            fresh.append(v)
        body = (
            instantiate(arg, fresh) if isinstance(arg, Abs) else App(arg, tuple(fresh))
        )
        self.check(inner, body, _instantiate(param.type, local))

    # -- helpers -----------------------------------------------------------------

    def _expect(self, ctx: Context, term: Term, actual: Term, expected: Term) -> None:
        if not self.defeq(actual, expected):
            raise TypingError(
                "%r has type %r, expected %r in %r" % (term, actual, expected, ctx)
            )


def _needed(param: Param) -> FrozenSet[Var]:
    """Pattern variables a premise mentions (other than its own)."""
    out = set()
    if param.type is not None:
        out |= free_vars(param.type)
    for _, a in param.hyps:
        out |= free_vars(a)
    out -= {x for x, _ in param.hyps}
    out.discard(param.var)
    return frozenset(v for v in out if v.name.startswith("?"))


def _rigid(schema: Term, pattern_vars: FrozenSet[Var]) -> bool:
    """True when ``schema`` is headed by a constant, so matching against
    it is meaningful (``?C(?p)`` is not: that would need unification)."""
    if isinstance(schema, Const):
        return True
    return isinstance(schema, App) and isinstance(schema.fn, Const)


def _instantiate(schema: Term, bindings: Dict[Var, Term]) -> Term:
    """Substitute bindings into a schema and tidy the beta-redexes this
    creates (``((x)B)(a)`` from a bound family applied to an argument)."""
    term = subst_many(
        schema, {v: t for v, t in bindings.items() if v in free_vars(schema)}
    )

    def tidy(t: Term, depth: int) -> Optional[Term]:
        if (
            isinstance(t, App)
            and isinstance(t.fn, Abs)
            and all(is_closed(a) for a in t.args)
        ):
            return transform(beta(t.fn, t.args), tidy, depth)
        return None

    return transform(term, tidy)
