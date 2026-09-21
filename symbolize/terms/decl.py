"""Declarations: what constants mean.

A ``Registry`` records, for each constant, its definition (unfolded by
delta-reduction) and its computation rules (iota-reduction, matched by
first-order pattern matching). Typing information is added in ``check.py``.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, FrozenSet, Iterable, List, Optional, Tuple

from .arity import A0, Arrow, cross
from .binding import free_vars, subst_many
from .term import (Abs, App, Comb, Const, Sel, Term, TermError, Var,
                   bound_occurrences)

SET = Const("Set")
"""The sort of sets (types). There are no universes: ``Set`` has no type."""


def pvar(name: str, arity=A0) -> Var:
    """A pattern variable for use in signatures and rules. The ``?`` prefix
    keeps it distinct from any user variable."""
    return Var("?" + name, arity)


class DeclarationError(TermError):
    """A declaration is malformed or clashes with an existing one."""


@dataclass(frozen=True)
class Definition:
    """A defined constant: ``const`` unfolds to ``body``.

    For a constant of arrow arity the body is an abstraction of the same
    arity, so that ``const(args)`` unfolds to ``body(args)`` and then
    beta-reduces.
    """

    const: Const
    body: Term

    def __post_init__(self) -> None:
        if self.body.arity != self.const.arity:
            raise DeclarationError(
                "Definition of %r has arity %r but body has %r"
                % (self.const, self.const.arity, self.body.arity)
            )
        if free_vars(self.body):
            raise DeclarationError(
                "Definition of %r has free variables %r"
                % (self.const, sorted(v.name for v in free_vars(self.body)))
            )


@dataclass(frozen=True)
class Rule:
    """A computation rule ``lhs -> rhs`` over pattern variables ``vars``.

    ``lhs`` must be headed by a constant applied to arguments. Arguments
    that are not bare pattern variables are *major*: the evaluator reduces
    the corresponding actual arguments to weak head normal form before
    matching.
    """

    lhs: App
    rhs: Term
    vars: FrozenSet[Var] = field(default=frozenset())

    def __post_init__(self) -> None:
        if not isinstance(self.lhs, App) or not isinstance(self.lhs.fn, Const):
            raise DeclarationError(
                "Rule lhs must be a constant applied to arguments: %r" % (self.lhs,)
            )
        if self.lhs.arity != self.rhs.arity:
            raise DeclarationError("Rule %r -> %r changes arity" % (self.lhs, self.rhs))
        pattern_vars = frozenset(self.vars) or free_vars(self.lhs)
        object.__setattr__(self, "vars", pattern_vars)
        if not free_vars(self.lhs) <= pattern_vars:
            raise DeclarationError(
                "Rule lhs %r has free variables that are not pattern variables"
                % (self.lhs,)
            )
        if not free_vars(self.rhs) <= pattern_vars:
            raise DeclarationError(
                "Rule rhs %r mentions variables not bound by the lhs" % (self.rhs,)
            )

    @property
    def head(self) -> Const:
        assert isinstance(self.lhs.fn, Const)
        return self.lhs.fn

    @property
    def major(self) -> Tuple[int, ...]:
        """Indices of the arguments that must be reduced before matching."""
        return tuple(
            i
            for i, a in enumerate(self.lhs.args)
            if not (isinstance(a, Var) and a in self.vars)
        )

    def match(self, term: App) -> Optional[Dict[Var, Term]]:
        """Match ``term`` against ``lhs``; return the substitution or None."""
        if term.fn != self.head or len(term.args) != len(self.lhs.args):
            return None
        bindings: Dict[Var, Term] = {}
        for pat, actual in zip(self.lhs.args, term.args):
            if not match(pat, actual, self.vars, bindings):
                return None
        return bindings

    def fire(self, bindings: Dict[Var, Term]) -> Term:
        """Instantiate ``rhs`` with the result of a successful ``match``."""
        return subst_many(self.rhs, bindings)


Equality = Callable[[Term, Term], bool]


def match(
    pat: Term,
    term: Term,
    pattern_vars: FrozenSet[Var],
    bindings: Dict[Var, Term],
    depth: int = 0,
    eq: Optional[Equality] = None,
) -> bool:
    """First-order matching of ``term`` against ``pat``, extending ``bindings``.

    A pattern variable under a binder only matches a subterm that does not
    mention that binder, so bindings are always locally closed. A pattern
    variable met twice must match equal terms, structurally or by ``eq``.
    """
    if isinstance(pat, Var) and pat in pattern_vars:
        if pat in bindings:
            return (eq or _structural)(bindings[pat], term)
        if term.arity != pat.arity:
            return False
        if any(b.index >= d + depth for b, d in bound_occurrences(term)):
            return False
        bindings[pat] = term
        return True
    if isinstance(pat, App):
        return (
            isinstance(term, App)
            and len(pat.args) == len(term.args)
            and match(pat.fn, term.fn, pattern_vars, bindings, depth, eq)
            and all(
                match(p, t, pattern_vars, bindings, depth, eq)
                for p, t in zip(pat.args, term.args)
            )
        )
    if isinstance(pat, Abs):
        return (
            isinstance(term, Abs)
            and pat.arities == term.arities
            and match(
                pat.body,
                term.body,
                pattern_vars,
                bindings,
                depth + len(pat.arities),
                eq,
            )
        )
    if isinstance(pat, Comb):
        return (
            isinstance(term, Comb)
            and len(pat.items) == len(term.items)
            and all(
                match(p, t, pattern_vars, bindings, depth, eq)
                for p, t in zip(pat.items, term.items)
            )
        )
    if isinstance(pat, Sel):
        return (
            isinstance(term, Sel)
            and pat.index == term.index
            and match(pat.term, term.term, pattern_vars, bindings, depth, eq)
        )
    # constants, bound variables, non-pattern free variables: structural
    return pat == term


def _structural(a: Term, b: Term) -> bool:
    return a == b


@dataclass(frozen=True)
class Param:
    """One premise of a typing rule, for one argument of a constant.

    ``var`` is the pattern variable standing for the argument. ``type`` is
    the schema the argument must inhabit (``SET`` for a set, ``None`` for a
    kind-only argument such as a motive whose family is not checked).
    ``hyps`` make the premise hypothetical for a higher-arity argument:
    ``var(x1, ..., xk) ∈ type [x1 ∈ A1, ..., xk ∈ Ak]`` as in [BN].
    """

    var: Var
    type: Optional[Term] = None
    hyps: Tuple[Tuple[Var, Term], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "hyps", tuple(self.hyps))
        if self.hyps:
            expected = Arrow(cross(*[x.arity for x, _ in self.hyps]), A0)
            if self.var.arity != expected:
                raise DeclarationError(
                    "Hypothetical premise for %r needs arity %r, not %r"
                    % (self.var, expected, self.var.arity)
                )


@dataclass(frozen=True)
class Signature:
    """The typing rule for a constant: premises for each argument, in order,
    and the type of the application. Pattern variables in ``result`` or in
    a premise that are not parameters are bound by matching against the
    inferred type of an argument (or the expected type, when checking)."""

    params: Tuple[Param, ...]
    result: Term

    def __post_init__(self) -> None:
        object.__setattr__(self, "params", tuple(self.params))
        seen = set()
        for p in self.params:
            if p.var in seen:
                raise DeclarationError("Duplicate parameter %r" % (p.var,))
            seen.add(p.var)

    @property
    def vars(self) -> FrozenSet[Var]:
        """All pattern variables mentioned by the signature."""
        out = set(free_vars(self.result))
        for p in self.params:
            out.add(p.var)
            if p.type is not None:
                out |= free_vars(p.type)
            for x, a in p.hyps:
                out.add(x)
                out |= free_vars(a)
        return frozenset(out)

    def check_arity(self, const: Const) -> None:
        """Ensure the premises fit the constant's arity."""
        if not self.params:
            if const.arity != A0:
                raise DeclarationError(
                    "%r has arity %r but its signature has no parameters"
                    % (const, const.arity)
                )
            return
        expected = cross(*[p.var.arity for p in self.params])
        if not isinstance(const.arity, Arrow) or const.arity.lhs != expected:
            raise DeclarationError(
                "%r has arity %r but its signature expects %r -> ..."
                % (const, const.arity, expected)
            )


@dataclass(frozen=True)
class TypeFormer:
    """A type former with its formation, introduction, elimination and
    computation rules, as tabulated in [BN] and [ST]."""

    former: Const
    formation: Signature
    constructors: Tuple[Tuple[Const, Signature], ...] = ()
    eliminators: Tuple[Tuple[Const, Signature], ...] = ()
    computation: Tuple[Rule, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "constructors", tuple(self.constructors))
        object.__setattr__(self, "eliminators", tuple(self.eliminators))
        object.__setattr__(self, "computation", tuple(self.computation))
        self.formation.check_arity(self.former)
        for c, sig in self.constructors + self.eliminators:
            sig.check_arity(c)
        heads = {c for c, _ in self.eliminators}
        for rule in self.computation:
            if rule.head not in heads:
                raise DeclarationError(
                    "Rule for %r but it is not an eliminator of %r"
                    % (rule.head, self.former)
                )

    @property
    def constants(self) -> Tuple[Const, ...]:
        return (self.former,) + tuple(
            c for c, _ in self.constructors + self.eliminators
        )


class Registry:
    """The declarations in scope: signatures, definitions and computation
    rules, plus which constants are constructors."""

    def __init__(self) -> None:
        self._signatures: Dict[Const, Signature] = {}
        self._definitions: Dict[Const, Definition] = {}
        self._rules: Dict[Const, List[Rule]] = {}
        self._major: Dict[Const, Tuple[int, ...]] = {}
        self._formers: Dict[Const, TypeFormer] = {}
        self._constructors: Dict[Const, Const] = {}

    def declare(self, const: Const, signature: Signature) -> None:
        """Register the typing rule of a primitive constant."""
        if const in self._signatures:
            raise DeclarationError("%r is already declared" % (const,))
        signature.check_arity(const)
        self._signatures[const] = signature

    def add_former(self, former: TypeFormer) -> TypeFormer:
        """Register a type former and all its constants and rules."""
        for c in former.constants:
            if c in self:
                raise DeclarationError("%r is already declared" % (c,))
        self.declare(former.former, former.formation)
        for c, sig in former.constructors:
            self.declare(c, sig)
            self._constructors[c] = former.former
        for c, sig in former.eliminators:
            self.declare(c, sig)
        for rule in former.computation:
            self.add_rule(rule.lhs, rule.rhs, rule.vars)
        self._formers[former.former] = former
        return former

    def define(
        self, const: Const, body: Term, signature: Optional[Signature] = None
    ) -> Definition:
        """Register ``const`` as an abbreviation for ``body``.

        A signature lets the checker type applications of ``const`` without
        unfolding it; otherwise it unfolds and checks the body.
        """
        if const in self:
            raise DeclarationError("%r is already declared" % (const,))
        definition = Definition(const, body)
        if signature is not None:
            self.declare(const, signature)
        self._definitions[const] = definition
        return definition

    def add_rule(self, lhs: App, rhs: Term, vars: Iterable[Var] = ()) -> Rule:
        """Register the computation rule ``lhs -> rhs``."""
        rule = Rule(lhs, rhs, frozenset(vars))
        if rule.head in self._definitions:
            raise DeclarationError(
                "%r is defined; it cannot also have rules" % (rule.head,)
            )
        self._rules.setdefault(rule.head, []).append(rule)
        self._major[rule.head] = tuple(
            sorted(set(self._major.get(rule.head, ())) | set(rule.major))
        )
        return rule

    def definition(self, const: Const) -> Optional[Definition]:
        return self._definitions.get(const)

    def signature(self, const: Const) -> Optional[Signature]:
        return self._signatures.get(const)

    def former(self, const: Const) -> Optional[TypeFormer]:
        return self._formers.get(const)

    def constructor_of(self, const: Const) -> Optional[Const]:
        """The former ``const`` is a constructor of, if any."""
        return self._constructors.get(const)

    def is_constructor(self, const: Const) -> bool:
        return const in self._constructors

    def rules(self, const: Const) -> Tuple[Rule, ...]:
        return tuple(self._rules.get(const, ()))

    def major(self, const: Const) -> Tuple[int, ...]:
        """Argument positions of ``const`` that rules inspect."""
        return self._major.get(const, ())

    def __contains__(self, const: object) -> bool:
        return (
            const in self._signatures
            or const in self._definitions
            or const in self._rules
        )
