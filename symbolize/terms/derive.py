"""Derivations: judgements ``a ∈ A [Γ]`` and the natural-deduction rules of
[ST] ch. 4 that build them.

A ``Judgement`` pairs a term with its type and the hypotheses it depends on.
Each rule validates its premises (with the checker and definitional
equality) and computes the conclusion's type from the premises' types, as
the rule tables in [ST] do -- so a conclusion is correct by construction
even when its term (a bare ``λ``, say) could not be re-inferred on its own.

The user-facing API is fluent: ``f(x)``, ``p.abstract(x)``, ``p.fst`` ...
with functions ``apply``, ``abstract``, ``pair`` ... behind them.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

import itertools

from typing import (
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from .arity import A0, Arrow, cross
from .binding import abstract as _abstract_term
from .binding import free_vars, instantiate, open_abs, subst, subst_many, transform
from .check import Checker, Context, TypingError
from .decl import (
    SET,
    Operators,
    Param,
    Provenance,
    Registry,
    Signature,
    axioms_used,
    pvar,
)
from .eval import Evaluator
from .library import STANDARD, Bool, Falsum
from .library import Id as _Id
from .library import J as _J
from .library import N, Pi, Plus, Sigma
from .library import abort as _abort
from .library import and_ as _and
from .library import apply as _apply
from .library import cases as _cases
from .library import exists as _exists
from .library import forall as _forall
from .library import fst as _fst
from .library import ifthenelse as _ifthenelse
from .library import implies as _implies
from .library import inl as _inl
from .library import inr as _inr
from .library import lam as _lam
from .library import natrec as _natrec
from .library import numeral as _numeral
from .library import not_ as _not
from .library import or_ as _or
from .library import pair as _pair
from .library import refl as _refl
from .library import snd as _snd
from .library import succ, zero
from .library.identity import cong as _cong
from .library.identity import symm as _symm
from .library.identity import trans as _trans
from .library.identity import transport as _transport
from .term import Abs, App, Const, Term, TermError, Var, _fresh_names


class DerivationError(TermError):
    """A rule was applied to premises that do not fit it."""


class Engine:
    """A registry with its evaluator and checker."""

    def __init__(self, registry: Registry = STANDARD):
        self.registry = registry
        self.evaluator = Evaluator(registry)
        self.checker = Checker(registry, self.evaluator)

    def whnf(self, term: Term) -> Term:
        return self.evaluator.whnf(term)

    def nf(self, term: Term) -> Term:
        return self.evaluator.nf(term)

    def defeq(self, a: Term, b: Term) -> bool:
        return self.evaluator.defeq(a, b)


DEFAULT = Engine()


# -- judgements -------------------------------------------------------------------


class Judgement:
    """``term ∈ type [ctx]``, or ``term set [ctx]`` when ``type`` is ``SET``.

    A *family* judgement (``hyps`` non-empty) is hypothetical:
    ``P(z) set [z ∈ N]``; its term has higher arity and it is applied with
    ``P(n)`` to give the set ``P(n)``.
    """

    __slots__ = ("ctx", "term", "type", "hyps", "engine", "aliases")

    def __init__(
        self,
        ctx: Context,
        term: Term,
        type: Term,
        hyps: Sequence[Tuple[Var, Term]] = (),
        engine: Engine = DEFAULT,
        check: bool = True,
        aliases: Optional[Dict[Term, str]] = None,
    ):
        self.ctx = ctx
        self.term = term
        self.type = type
        self.hyps = tuple(hyps)
        self.engine = engine
        self.aliases: Dict[Term, str] = dict(aliases or {})
        if check and not self.hyps:
            engine.checker.check(ctx, term, type)

    # -- classification ----------------------------------------------------------

    @property
    def is_set(self) -> bool:
        return self.type == SET and not self.hyps

    @property
    def is_family(self) -> bool:
        return bool(self.hyps)

    @property
    def is_hypothesis(self) -> bool:
        """A variable assumed in its own context."""
        return isinstance(self.term, Var) and self.term in self.ctx

    # -- equality and display ----------------------------------------------------

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Judgement)
            and self.term == other.term
            and self.type == other.type
            and self.hyps == other.hyps
            and self.ctx == other.ctx
        )

    def __hash__(self) -> int:
        return hash((self.term, self.type, self.hyps))

    def has_type(self, type: Union["Judgement", Term]) -> bool:
        """Definitional comparison of this judgement's type with ``type``."""
        return self.engine.defeq(self.type, _term_of(type))

    def defeq(self, other: Union["Judgement", Term]) -> bool:
        """Definitional comparison of the terms."""
        return self.engine.defeq(self.term, _term_of(other))

    def __repr__(self) -> str:
        if self.is_family:
            args = ", ".join(x.name for x, _ in self.hyps)
            hyps = ", ".join("%r ∈ %r" % (x, a) for x, a in self.hyps)
            return "%r(%s) set [%s]" % (self.term, args, hyps)
        if self.is_set:
            return "%r set" % (self.term,)
        return "%r : %r" % (self.term, self.type)

    def repr_full(self) -> str:
        """Include the hypotheses."""
        return "%r  %r" % (self, self.ctx)

    # -- trust -----------------------------------------------------------------

    @property
    def axioms(self) -> Tuple[Const, ...]:
        """The axioms this proof depends on, definitions unfolded.

        Hypotheses are not included: ``ctx`` already shows what is assumed.
        """
        return axioms_used(self.term, self.engine.registry)

    def trust_report(self) -> str:
        """What this judgement is believed on, rather than proved from."""
        used = self.axioms
        if not used:
            return "%s depends on no axioms" % (self.repr_unicode(),)
        lines = ["%s depends on %d axiom(s):" % (self.repr_unicode(), len(used))]
        width = max(len(c.name) for c in used)
        for c in used:
            record = self.engine.registry.provenance(c)
            lines.append("  %-*s  %s" % (width, c.name, record or "local"))
        return "\n".join(lines)

    # -- rendering -------------------------------------------------------------

    def alias(self, name: str) -> "Judgement":
        """Display this judgement's term as ``name`` (rendering only)."""
        aliases = dict(self.aliases)
        aliases[self.term] = name
        return Judgement(
            self.ctx, self.term, self.type, self.hyps, self.engine, False, aliases
        )

    def _renderer(self, style: str):
        from .render.text import TextRenderer

        return TextRenderer(style, self.aliases)

    def repr_typestring(self) -> str:
        return self._renderer("typestring").render_judgement(self)

    def repr_unicode(self) -> str:
        return self._renderer("unicode").render_judgement(self)

    def repr_latex(self) -> str:
        return self._renderer("latex").render_judgement(self)

    def repr_context(self, style: str = "unicode") -> str:
        return self._renderer(style).render_context(self.ctx)

    def _repr_latex_(self) -> str:
        """For Jupyter/IPython."""
        return "$$%s$$" % self.repr_latex()

    # -- rules as methods ---------------------------------------------------------

    def __call__(self, *args: "Judgement") -> "Judgement":
        """Application: ⇒E / ∀E for proofs, or a family applied to elements."""
        if self.is_family:
            return apply_family(self, *args)
        result = self
        for a in args:
            result = apply(result, a)
        return result

    def abstract(self, *variables: "Judgement") -> "Judgement":
        """⇒I / ∀I, discharging ``variables`` (last one innermost)."""
        result = self
        for v in reversed(variables):
            result = abstract(result, v)
        return result

    def pair(self, other: "Judgement", family: Optional[Term] = None) -> "Judgement":
        return pair(self, other, family)

    @property
    def fst(self) -> "Judgement":
        return fst(self)

    @property
    def snd(self) -> "Judgement":
        return snd(self)

    def inl(self, other: "Judgement") -> "Judgement":
        return inl(self, other)

    def inr(self, other: "Judgement") -> "Judgement":
        return inr(self, other)

    def cases(self, f: "Judgement", g: "Judgement") -> "Judgement":
        return cases(self, f, g)

    def abort(self, set_: "Judgement") -> "Judgement":
        return abort(self, set_)

    def eq(self, other: "Side") -> "Judgement":
        """The set ``Id(A, self, other)``; ``other`` may be an int literal
        or a term of ``A``, as in ``(x + 1).eq(0)``."""
        return eq(self, other)

    @property
    def refl(self) -> "Judgement":
        return refl(self)

    @property
    def symm(self) -> "Judgement":
        return symm(self)

    def trans(self, other: "Judgement") -> "Judgement":
        return trans(self, other)

    def cong(self, p: "Judgement") -> "Judgement":
        """``f.cong(p)``: congruence of this function over the identity ``p``."""
        return cong(self, p)

    def cong_in(self, context: Abs) -> "Judgement":
        """``p.cong_in((x)t)``: congruence of a term context over ``p``."""
        return cong_in(context, self)

    def transport(self, p: "Judgement", c: "Judgement") -> "Judgement":
        """``P.transport(p, c)``: carry ``c`` along ``p``."""
        return transport(self, p, c)

    def rewrite(
        self, p: "Judgement", at: Optional[Sequence[int]] = None
    ) -> "Judgement":
        """``t.rewrite(p)``: rewrite this judgement's type with ``p``."""
        return rewrite(self, p, at)

    rw = rewrite

    def subst(self, var: "Judgement", value: "Judgement") -> "Judgement":
        return substitute(self, var, value)

    # -- equations -------------------------------------------------------------
    #
    # Balanced manipulation, as sympy users do with Eq: on a proof h : a = b,
    # each step yields a proof of the new equation (h + 1 : a + 1 = b + 1),
    # by congruence and so without new axioms. Only forward steps are free;
    # undoing one (cancelling, dividing) needs a law.

    @property
    def is_equation(self) -> bool:
        """A proof of an equation ``a = b`` (not the statement ``a = b``)."""
        return _equation(self) is not None

    @property
    def lhs(self) -> "Judgement":
        """The left side of an equation, or of a proof of one."""
        return _sides(self)[0]

    @property
    def rhs(self) -> "Judgement":
        """The right side of an equation, or of a proof of one."""
        return _sides(self)[1]

    def flip(self) -> "Judgement":
        """``b = a``: ``symm`` of a proof, or the statement turned round."""
        return flip(self)

    def subs(self, p: "Judgement", at: Where = "both") -> "Judgement":
        """Replace ``p``'s left side by its right side, in this proof's
        equation: ``at`` is ``"lhs"``, ``"rhs"`` or ``"both"``, or the
        occurrence indices ``rewrite`` takes."""
        return subs(self, p, at)

    def lhs_by(self, p: "Judgement") -> "Judgement":
        """``a′ = b`` from this ``a = b`` and ``p`` relating ``a`` and
        ``a′`` (either way round)."""
        return lhs_by(self, p)

    def rhs_by(self, p: "Judgement") -> "Judgement":
        """``a = b′`` from this ``a = b`` and ``p`` relating ``b`` and
        ``b′`` (either way round)."""
        return rhs_by(self, p)

    def assume(self, name: Optional[str] = None) -> "Judgement":
        """A hypothesis of this set, named ``h``, ``h'``... unless named."""
        return assume(self, name)

    def discharge(self, *hypotheses: "Judgement") -> "Judgement":
        """⇒I over the given hypotheses: ``h2.discharge(h)`` turns what was
        derived from ``h : e`` into the theorem ``e ⇒ e′``."""
        return self.abstract(*hypotheses)

    # -- computation ---------------------------------------------------------------

    def run(self) -> "Judgement":
        """Normalise the term (subject reduction keeps the type)."""
        return self._with_term(self.engine.nf(self.term))

    normalise = run

    def whnf(self) -> "Judgement":
        return self._with_term(self.engine.whnf(self.term))

    def _with_term(self, term: Term) -> "Judgement":
        return Judgement(
            self.ctx, term, self.type, self.hyps, self.engine, False, self.aliases
        )

    # -- connectives on sets -----------------------------------------------------

    def __rshift__(self, other: "Judgement") -> "Judgement":
        return implies(self, other)

    def __and__(self, other: "Judgement") -> "Judgement":
        return and_(self, other)

    def __or__(self, other: "Judgement") -> "Judgement":
        return or_(self, other)

    def __invert__(self) -> "Judgement":
        return not_(self)

    def hyp(self, name: str) -> "Judgement":
        """A hypothesis ``name ∈ self`` (for a set judgement)."""
        return hyp(name, self)

    # -- arithmetic on elements ------------------------------------------------
    #
    # Each builds the term and nothing more: x + 1 is add(x, 1), never
    # simplified. An int operand is the literal of the other operand's set.
    # Anything else is NotImplemented, so Python raises its usual TypeError.

    def __add__(self, other: object) -> "Judgement":
        return _binary("add", self, other)

    def __radd__(self, other: object) -> "Judgement":
        return _binary("add", other, self)

    def __mul__(self, other: object) -> "Judgement":
        return _binary("mul", self, other)

    def __rmul__(self, other: object) -> "Judgement":
        return _binary("mul", other, self)

    def __sub__(self, other: object) -> "Judgement":
        return _binary("sub", self, other)

    def __rsub__(self, other: object) -> "Judgement":
        return _binary("sub", other, self)

    def __neg__(self) -> "Judgement":
        return negate(self)

    def __pow__(self, exponent: object) -> "Judgement":
        if not _is_operand(exponent):
            return NotImplemented
        return power(self, exponent)  # type: ignore[arg-type]

    # -- spellings from the previous API -------------------------------------

    get_proof = hyp

    def apply(self, *args: object) -> "Judgement":
        """``f.apply(a)`` is ``f(a)``; on a proof of ``a = b``,
        ``h.apply(f)`` is ``f(a) = f(b)``, ``f`` a function judgement, an
        abstraction or a Python function (``h.apply(lambda t: t ** 2)``)."""
        if len(args) == 1 and self.is_equation:
            f = args[0]
            if isinstance(f, Judgement):
                return cong(f, self)
            return cong_in(f, self)  # type: ignore[arg-type]
        return self(*args)  # type: ignore[arg-type]

    def select(self, i: int) -> "Judgement":
        """``p.select(0)`` / ``p.select(1)`` are ``fst`` / ``snd``."""
        if i == 0:
            return fst(self)
        if i == 1:
            return snd(self)
        raise DerivationError("select: index must be 0 or 1")


# -- hypotheses -------------------------------------------------------------------


def set_var(name: str, engine: Engine = DEFAULT) -> Judgement:
    """A set assumed outright: ``A set [A ∈ Set]``."""
    var = Var(name)
    return Judgement(Context().extend(var, SET), var, SET, engine=engine)


def family(name: str, *over: Judgement, engine: Engine = DEFAULT) -> Judgement:
    """A family of sets over the given sets: ``P(z) set [z ∈ A]``."""
    if not over:
        return set_var(name, engine)
    for s in over:
        _require_set(s)
    var = Var(name, Arrow(cross(*[A0] * len(over)), A0))
    ctx = merge(*[s.ctx for s in over])
    names = _fresh_names(["z"] * len(over), (), ctx.names() | {name})
    hyps = tuple((Var(n), s.term) for n, s in zip(names, over))
    ctx = ctx.extend(var, SET, hyps)
    return Judgement(ctx, var, SET, hyps, engine, check=False)


def hyp(name: str, set_: Judgement) -> Judgement:
    """A hypothesis ``name ∈ set_``: the assumption rule."""
    _require_set(set_)
    var = Var(name)
    if var in set_.ctx:
        raise DerivationError("%r is already a hypothesis" % (var,))
    ctx = set_.ctx.extend(var, set_.term)
    return Judgement(ctx, var, set_.term, engine=set_.engine, check=False)


def judge(
    term: Term,
    type: Term,
    ctx: Context = Context(),
    engine: Engine = DEFAULT,
) -> Judgement:
    """A judgement checked from scratch by the type checker."""
    return Judgement(ctx, term, type, engine=engine)


# -- set formation ------------------------------------------------------------------


def _form(const: Const, *sets: Judgement) -> Judgement:
    for s in sets:
        _require_set(s)
    engine = sets[0].engine
    ctx = merge(*[s.ctx for s in sets])
    return Judgement(ctx, const(*[s.term for s in sets]), SET, engine=engine)


def implies(a: Judgement, b: Judgement) -> Judgement:
    return _form(_implies, a, b)


def and_(a: Judgement, b: Judgement) -> Judgement:
    return _form(_and, a, b)


def or_(a: Judgement, b: Judgement) -> Judgement:
    return _form(_or, a, b)


def not_(a: Judgement) -> Judgement:
    return _form(_not, a)


def _quantify(const: Const, x: Judgement, body: Judgement) -> Judgement:
    """``∀(A, (x)B)`` / ``∃(A, (x)B)``: ``x`` a hypothesis or ``body`` a family."""
    if body.is_family:
        _require_set(x)
        if len(body.hyps) != 1:
            raise DerivationError("Quantification needs a family of one argument")
        ctx = merge(x.ctx, body.ctx)
        return Judgement(ctx, const(x.term, body.term), SET, engine=x.engine)
    _require_hypothesis(x)
    _require_set(body)
    fam = _abstract_term(body.term, [x.term])
    ctx = discharge(body.ctx, x.term)
    return Judgement(ctx, const(x.type, fam), SET, engine=body.engine)


def forall(x: Judgement, body: Judgement) -> Judgement:
    return _quantify(_forall, x, body)


def exists(x: Judgement, body: Judgement) -> Judgement:
    return _quantify(_exists, x, body)


def eq(a: Side, b: Side) -> Judgement:
    """Id-formation: ``a ∈ A``, ``b ∈ A``  ⊢  ``Id(A, a, b) set``.

    One side may be an int literal of ``A``'s arithmetic, or a bare term,
    which is checked against the other side's set in its context:
    ``x.eq(0)`` and ``x.eq(REAL.zero)`` both state ``x = 0``.
    """
    if not isinstance(a, Judgement):
        if not isinstance(b, Judgement):
            raise DerivationError(
                "Cannot tell the set of %r = %r: neither side is a judgement"
                % (a, b)
            )
        a = _side(a, b)
    else:
        b = _side(b, a)
    engine = a.engine
    if not engine.defeq(a.type, b.type):
        raise DerivationError(
            "%r and %r are elements of different sets: %r and %r"
            % (a, b, a.type, b.type)
        )
    return Judgement(
        merge(a.ctx, b.ctx),
        _Id(a.type, a.term, b.term),
        SET,
        engine=engine,
        check=False,
        aliases=_aliases(a, b),
    )


def _side(x: Side, other: Judgement) -> Judgement:
    """``x`` as an element of ``other``'s set, for one side of an equation."""
    if isinstance(x, Judgement):
        return x
    if isinstance(x, Term):
        return Judgement(other.ctx, x, other.type, engine=other.engine)
    if _is_operand(x):
        return _element(x, operators(other), other)
    raise DerivationError("Cannot equate %r with %r" % (other, x))


def apply_family(fam: Judgement, *args: Judgement) -> Judgement:
    """``P(a) set`` from ``P(z) set [z ∈ A]`` and ``a ∈ A``."""
    if len(args) != len(fam.hyps):
        raise DerivationError(
            "%r takes %d arguments, got %d" % (fam.term, len(fam.hyps), len(args))
        )
    ctx = merge(fam.ctx, *[a.ctx for a in args])
    term = fam.term(*[a.term for a in args])
    return Judgement(ctx, term, SET, engine=fam.engine)


# -- the rules ----------------------------------------------------------------------


def apply(f: Judgement, a: Judgement) -> Judgement:
    """⇒E / ∀E: ``f ∈ Π(A, B)``, ``a ∈ A``  ⊢  ``apply(f, a) ∈ B(a)``."""
    engine = f.engine
    dom, fam = _expect_former(f, Pi, "a function")
    _expect_type(a, dom)
    ctx = merge(f.ctx, a.ctx)
    return Judgement(
        ctx,
        _apply(f.term, a.term),
        _at(fam, a.term),
        engine=engine,
        check=False,
        aliases=_aliases(f, a),
    )


def abstract(b: Judgement, x: Judgement) -> Judgement:
    """⇒I / ∀I: ``b ∈ B [x ∈ A]``  ⊢  ``λ((x)b) ∈ A ⇒ B`` (or ``∀(A, (x)B)``)."""
    _require_hypothesis(x)
    var = x.term
    assert isinstance(var, Var)
    if var in b.ctx:
        entry = b.ctx.lookup(var)
        assert entry is not None and entry.type is not None
        if not b.engine.defeq(entry.type, x.type):
            raise DerivationError(
                "%r is assumed with type %r in %r, not %r"
                % (var, entry.type, b, x.type)
            )
    # a vacuous discharge (x not used by b) is allowed, as in [ST]; the
    # hypotheses x's own set depends on are kept
    ctx = discharge(merge(b.ctx, x.ctx), var)
    term = _lam(_abstract_term(b.term, [var]))
    if var in b.type:
        type = _forall(x.type, _abstract_term(b.type, [var]))
    else:
        type = _implies(x.type, b.type)
    return Judgement(
        ctx, term, type, engine=b.engine, check=False, aliases=_aliases(b, x)
    )


def pair(a: Judgement, b: Judgement, family: Optional[Term] = None) -> Judgement:
    """∧I / ∃I: ``a ∈ A``, ``b ∈ B(a)``  ⊢  ``pair(a, b) ∈ Σ(A, B)``.

    The result is ``A ∧ B`` unless ``a`` is a hypothesis ``x`` occurring in
    the type of ``b``, in which case it is ``∃(A, (x)B)``; pass ``family``
    to choose the dependency explicitly.
    """
    engine = a.engine
    ctx = merge(a.ctx, b.ctx)
    term = _pair(a.term, b.term)
    if family is not None:
        _expect_type(b, _at(family, a.term))
        return Judgement(
            ctx,
            term,
            _exists(a.type, family),
            engine=engine,
            check=False,
            aliases=_aliases(a, b),
        )
    if isinstance(a.term, Var) and a.term in b.type:
        fam = _abstract_term(b.type, [a.term])
        return Judgement(
            ctx,
            term,
            _exists(a.type, fam),
            engine=engine,
            check=False,
            aliases=_aliases(a, b),
        )
    return Judgement(
        ctx,
        term,
        _and(a.type, b.type),
        engine=engine,
        check=False,
        aliases=_aliases(a, b),
    )


def fst(p: Judgement) -> Judgement:
    """∧E / ∃E: ``p ∈ Σ(A, B)``  ⊢  ``fst(p) ∈ A``."""
    dom, _ = _expect_former(p, Sigma, "a pair")
    return Judgement(
        p.ctx, _fst(p.term), dom, engine=p.engine, check=False, aliases=_aliases(p)
    )


def snd(p: Judgement) -> Judgement:
    """∧E / ∃E: ``p ∈ Σ(A, B)``  ⊢  ``snd(p) ∈ B(fst(p))``."""
    _, fam = _expect_former(p, Sigma, "a pair")
    return Judgement(
        p.ctx,
        _snd(p.term),
        _at(fam, _fst(p.term)),
        engine=p.engine,
        check=False,
        aliases=_aliases(p),
    )


def inl(a: Judgement, b_set: Judgement) -> Judgement:
    """∨I: ``a ∈ A``, ``B set``  ⊢  ``inl(a) ∈ A ∨ B``."""
    _require_set(b_set)
    ctx = merge(a.ctx, b_set.ctx)
    return Judgement(
        ctx,
        _inl(a.term),
        _or(a.type, b_set.term),
        engine=a.engine,
        check=False,
        aliases=_aliases(a),
    )


def inr(b: Judgement, a_set: Judgement) -> Judgement:
    """∨I: ``b ∈ B``, ``A set``  ⊢  ``inr(b) ∈ A ∨ B``."""
    _require_set(a_set)
    ctx = merge(b.ctx, a_set.ctx)
    return Judgement(
        ctx,
        _inr(b.term),
        _or(a_set.term, b.type),
        engine=b.engine,
        check=False,
        aliases=_aliases(b),
    )


def cases(p: Judgement, f: Judgement, g: Judgement) -> Judgement:
    """∨E: ``p ∈ A ∨ B``, ``f ∈ A ⇒ C``, ``g ∈ B ⇒ C``  ⊢  ``cases(p, f, g) ∈ C``."""
    engine = p.engine
    a, b = _expect_former(p, Plus, "a disjunction")
    fa, fc = _expect_former(f, Pi, "a function")
    gb, gc = _expect_former(g, Pi, "a function")
    if not engine.defeq(fa, a):
        raise DerivationError("%r does not accept the left disjunct %r" % (f, a))
    if not engine.defeq(gb, b):
        raise DerivationError("%r does not accept the right disjunct %r" % (g, b))
    c = _constant_codomain(fc, f)
    if not engine.defeq(c, _constant_codomain(gc, g)):
        raise DerivationError("%r and %r have different conclusions" % (f, g))
    ctx = merge(p.ctx, f.ctx, g.ctx)
    return Judgement(
        ctx,
        _cases(p.term, f.term, g.term),
        c,
        engine=engine,
        check=False,
        aliases=_aliases(p, f, g),
    )


def abort(p: Judgement, set_: Judgement) -> Judgement:
    """⊥E: ``p ∈ ⊥``, ``A set``  ⊢  ``abort(A, p) ∈ A``."""
    _require_set(set_)
    if not p.engine.defeq(p.type, Falsum):
        raise DerivationError("%r is not a proof of ⊥" % (p,))
    ctx = merge(p.ctx, set_.ctx)
    return Judgement(
        ctx,
        _abort(set_.term, p.term),
        set_.term,
        engine=p.engine,
        check=False,
        aliases=_aliases(p),
    )


def natrec(
    n: Judgement, d: Judgement, f: Judgement, motive: Optional[Term] = None
) -> Judgement:
    """N-elimination in the form of [ST] p100 (``prim``):

    ``n ∈ N``, ``d ∈ C(0)``, ``f ∈ ∀x.(C(x) ⇒ C(succ(x)))``  ⊢
    ``natrec(C, n, d, (x, y)f(x)(y)) ∈ C(n)``.

    The motive ``C`` is read off the type of ``f`` unless given.
    """
    engine = n.engine
    _expect_type(n, N)
    if motive is None:
        motive = _motive_from_step(f)
    _expect_type(d, _at(motive, zero))
    avoid = {v.name for v in free_vars(f.term)}
    x, y = (Var(nm) for nm in _fresh_names(["x", "y"], (), avoid))
    step = _applied(_applied(f.term, x), y).abstract(x, y)
    _expect_type(
        f, _forall(N, _implies(_at(motive, x), _at(motive, succ(x))).abstract(x))
    )
    ctx = merge(n.ctx, d.ctx, f.ctx)
    term = _natrec(motive, n.term, d.term, step)
    return Judgement(
        ctx,
        term,
        _at(motive, n.term),
        engine=engine,
        check=False,
        aliases=_aliases(n, d, f),
    )


prim = natrec


def ifthenelse(b: Judgement, c: Judgement, d: Judgement) -> Judgement:
    """Bool-elimination [ST] p97: ``b ∈ Bool``, ``c, d ∈ C``  ⊢  ``ifthenelse(b, c, d) ∈ C``."""
    _expect_type(b, Bool)
    if not c.engine.defeq(c.type, d.type):
        raise DerivationError("%r and %r have different types" % (c, d))
    ctx = merge(b.ctx, c.ctx, d.ctx)
    term = _ifthenelse(b.term, c.term, d.term)
    return Judgement(
        ctx, term, c.type, engine=b.engine, check=False, aliases=_aliases(b, c, d)
    )


def substitute(b: Judgement, x: Judgement, a: Judgement) -> Judgement:
    """Substitution: ``b ∈ B [x ∈ A]``, ``a ∈ A``  ⊢  ``b[x := a] ∈ B[x := a]``."""
    _require_hypothesis(x)
    var = x.term
    assert isinstance(var, Var)
    if var not in b.ctx:
        raise DerivationError("%r is not a hypothesis of %r" % (var, b))
    _expect_type(a, x.type)
    ctx = Context()
    for entry in b.ctx.entries:
        if entry.var == var:
            continue
        assert entry.type is not None
        ctx = ctx.extend(
            entry.var,
            subst(entry.type, var, a.term),
            tuple((z, subst(t, var, a.term)) for z, t in entry.hyps),
        )
    ctx = merge(ctx, a.ctx)
    return Judgement(
        ctx,
        subst(b.term, var, a.term),
        subst(b.type, var, a.term),
        engine=b.engine,
        check=False,
    )


# -- arithmetic ---------------------------------------------------------------------
#
# Terms carry no types, so the operators live on judgements, which do: the
# set an element belongs to selects the Operators registered for it (see
# decl.Operators). The operation's signature was checked against the carrier
# when the operators were registered, so the results are well typed by
# construction, as the rules' conclusions are.

Operand = Union[Judgement, int]

# one side of an equation: an operand, or a bare term of the other's set
Side = Union[Judgement, int, Term]


def _is_operand(x: object) -> bool:
    return isinstance(x, Judgement) or (
        isinstance(x, int) and not isinstance(x, bool)
    )


def operators(j: Judgement) -> Operators:
    """The arithmetic of the set ``j`` is an element of."""
    if j.is_set and _identity(j.engine, j.term) is not None:
        raise DerivationError(
            "%s is the statement of an equation, not a proof of it; assume it"
            " (e.assume()) or prove it, then manipulate the proof"
            % (j.repr_unicode(),)
        )
    if j.is_set or j.is_family:
        raise DerivationError(
            "%s is a set; arithmetic is on its elements (∨ of sets is |)"
            % (j.repr_unicode(),)
        )
    registry = j.engine.registry
    found = registry.operators(j.type)
    if found is None:
        found = registry.operators(j.engine.whnf(j.type))
    if found is None:
        raise DerivationError(
            "No arithmetic is declared on %s" % (j.type.repr_unicode(),)
        )
    return found


def literal(k: int, set_: Judgement) -> Judgement:
    """The element of ``set_`` denoted by the integer literal ``k``."""
    _require_set(set_)
    ops = set_.engine.registry.operators(set_.term)
    if ops is None:
        raise DerivationError(
            "No arithmetic is declared on %s" % (set_.term.repr_unicode(),)
        )
    return Judgement(Context(), ops.literal(k), ops.carrier, engine=set_.engine)


def _element(x: Operand, ops: Operators, like: Judgement) -> Judgement:
    """``x`` as an element of ``ops.carrier``: a literal, or checked."""
    if isinstance(x, Judgement):
        _expect_type(x, ops.carrier)
        return x
    return Judgement(Context(), ops.literal(x), ops.carrier, engine=like.engine)


def _operation(ops: Operators, name: str) -> Const:
    const = getattr(ops, name)
    if const is None:
        raise DerivationError(
            "%s has no %s" % (ops.carrier.repr_unicode(), _SPOKEN[name])
        )
    return const


_SPOKEN = {
    "add": "addition",
    "mul": "multiplication",
    "sub": "subtraction",
    "neg": "negation",
    "pow": "powers",
}


def _binary(name: str, a: object, b: object) -> Judgement:
    if not (_is_operand(a) and _is_operand(b)):
        return NotImplemented  # type: ignore[return-value]
    if _is_equation(a) or _is_equation(b):
        return _balanced(name, a, b)  # type: ignore[arg-type]
    anchor = a if isinstance(a, Judgement) else b
    assert isinstance(anchor, Judgement)
    ops = operators(anchor)
    const = _operation(ops, name)
    x = _element(a, ops, anchor)  # type: ignore[arg-type]
    y = _element(b, ops, anchor)  # type: ignore[arg-type]
    return Judgement(
        merge(x.ctx, y.ctx),
        const(x.term, y.term),
        ops.carrier,
        engine=anchor.engine,
        check=False,
        aliases=_aliases(x, y),
    )


def add(a: Operand, b: Operand) -> Judgement:
    """``a + b`` in the set of whichever operand is a judgement."""
    return _binary("add", a, b)


def mul(a: Operand, b: Operand) -> Judgement:
    """``a ⋅ b``."""
    return _binary("mul", a, b)


def sub(a: Operand, b: Operand) -> Judgement:
    """``a - b``."""
    return _binary("sub", a, b)


def negate(a: Judgement) -> Judgement:
    """``-a``; for a proof of ``a = b``, ``-a = -b``."""
    if _is_equation(a):
        return cong_in(lambda t: negate(t), a)
    const = _operation(operators(a), "neg")
    return Judgement(
        a.ctx,
        const(a.term),
        a.type,
        engine=a.engine,
        check=False,
        aliases=_aliases(a),
    )


def power(base: Judgement, exponent: Union[Judgement, int]) -> Judgement:
    """``base^exponent``, the exponent a natural number or an element of N;
    for a proof of ``a = b``, ``a^n = b^n``."""
    if _is_equation(base):
        return cong_in(lambda t: power(t, exponent), base)
    ops = operators(base)
    const = _operation(ops, "pow")
    if isinstance(exponent, Judgement):
        _expect_type(exponent, N)
        n = exponent
    elif exponent < 0:
        raise DerivationError(
            "%d is not a natural number; negative powers need a field"
            % exponent
        )
    else:
        n = Judgement(
            Context(), _numeral(exponent), N, engine=base.engine, check=False
        )
    return Judgement(
        merge(base.ctx, n.ctx),
        const(base.term, n.term),
        ops.carrier,
        engine=base.engine,
        check=False,
        aliases=_aliases(base, n),
    )


def symbols(
    names: str, set_: Judgement
) -> Union[Judgement, Tuple[Judgement, ...]]:
    """Hypotheses ``x, y, ... ∈ set_``, as sympy's ``symbols``.

    ``names`` is split on spaces and commas; one name gives one judgement,
    several give a tuple: ``x, y = symbols("x y", R)``.
    """
    split = [n for n in names.replace(",", " ").split() if n]
    if not split:
        raise DerivationError("symbols needs at least one name")
    made = tuple(hyp(n, set_) for n in split)
    return made[0] if len(made) == 1 else made


def cite(
    const: Const, *args: Judgement, engine: Optional[Engine] = None
) -> Judgement:
    """A declared constant -- an axiom or law, typically -- used at ``args``.

    ``cite(REAL.add_comm, x, y)`` is ``x + y = y + x``. The conclusion is
    the constant's signature instantiated at the arguments, found and
    checked by the type checker, so citing a law at elements of the wrong
    set is refused.
    """
    if args:
        engine = args[0].engine
    elif engine is None:
        engine = DEFAULT
    ctx = merge(*[a.ctx for a in args])
    term = const(*[a.term for a in args]) if args else const
    try:
        type = engine.checker.infer(ctx, term)
    except TypingError as error:
        raise DerivationError("Cannot cite %r here: %s" % (const, error))
    return Judgement(
        ctx, term, type, engine=engine, check=False, aliases=_aliases(*args)
    )


# -- equations -----------------------------------------------------------------
#
# The sympy Eq workflow on proofs. Each function returns a judgement whose
# term says how the new equation follows from the old, by the derived
# rules of identity.py, so none adds an axiom.

Where = Union[str, Sequence[int]]


def _identity(engine: Engine, t: Term) -> Optional[Tuple[Term, Term, Term]]:
    """``(A, a, b)`` when ``t`` is (or unfolds to) ``Id(A, a, b)``."""
    t = engine.whnf(t)
    if isinstance(t, App) and t.fn == _Id:
        return t.args[0], t.args[1], t.args[2]
    return None


def _equation(j: object) -> Optional[Tuple[Term, Term, Term]]:
    """The endpoints of ``j`` if it is a proof of an equation."""
    if not isinstance(j, Judgement) or j.is_set or j.is_family:
        return None
    return _identity(j.engine, j.type)


def _is_equation(j: object) -> bool:
    return _equation(j) is not None


def _sides(j: Judgement) -> Tuple[Judgement, Judgement]:
    """Both sides of an equation statement or proof, as judgements whose
    contexts keep only the hypotheses each side mentions."""
    found = _identity(j.engine, j.term) if j.is_set else _equation(j)
    if found is None:
        raise DerivationError("%r is not an equation" % (j,))
    A, a, b = found
    return tuple(  # type: ignore[return-value]
        Judgement(
            _restrict(j.ctx, side),
            side,
            A,
            engine=j.engine,
            check=False,
            aliases=_aliases(j),
        )
        for side in (a, b)
    )


def _restrict(ctx: Context, term: Term) -> Context:
    """The entries of ``ctx`` that ``term`` needs, transitively, in order."""
    needed = set(free_vars(term))
    keep: List[Param] = []
    for entry in reversed(ctx.entries):
        if entry.var not in needed:
            continue
        keep.append(entry)
        if entry.type is not None:
            needed |= free_vars(entry.type)
        for z, t in entry.hyps:
            needed |= free_vars(t)
            needed.discard(z)
    return Context(list(reversed(keep)))


def flip(j: Judgement) -> Judgement:
    """``b = a`` from ``a = b``: ``symm`` of a proof, or a statement turned
    round (still only a statement)."""
    if j.is_set:
        found = _identity(j.engine, j.term)
        if found is None:
            raise DerivationError("%r is not an equation" % (j,))
        A, a, b = found
        return Judgement(
            j.ctx,
            _Id(A, b, a),
            SET,
            engine=j.engine,
            check=False,
            aliases=_aliases(j),
        )
    return symm(j)


def _balanced(name: str, a: Operand, b: Operand) -> Judgement:
    """The operation ``name`` applied to both sides.

    With one proof ``h : a = b`` and an operand ``c``, congruence gives
    ``a ∘ c = b ∘ c`` (or ``c ∘ a = c ∘ b``). With two, ``h : a = b`` and
    ``g : c = d``, it is ``a ∘ c = b ∘ c = b ∘ d`` joined by ``trans``.
    """

    def op(u: Operand, v: Operand) -> Judgement:
        return _binary(name, u, v)

    if _is_equation(a) and _is_equation(b):
        assert isinstance(a, Judgement) and isinstance(b, Judgement)
        c, right = b.lhs, a.rhs
        return trans(
            cong_in(lambda t: op(t, c), a),
            cong_in(lambda t: op(right, t), b),
        )
    if _is_equation(a):
        assert isinstance(a, Judgement)
        return cong_in(lambda t: op(t, b), a)
    assert isinstance(b, Judgement)
    return cong_in(lambda t: op(a, t), b)


def subs(target: Judgement, p: Judgement, at: Where = "both") -> Judgement:
    """Rewrite ``target`` with ``p : c = d``, replacing ``c`` by ``d``.

    For a proof of an equation, ``at`` may name the side: ``"lhs"``,
    ``"rhs"`` or ``"both"``; otherwise it is the occurrence indices of
    ``rewrite``. ``p.flip()`` substitutes the other way.
    """
    if target.is_set:
        raise DerivationError(
            "%s is a statement; substitution needs a proof of it (assume it"
            " first)" % (target.repr_unicode(),)
        )
    if not isinstance(at, str):
        return rewrite(target, p, at)
    if at not in ("lhs", "rhs", "both"):
        raise DerivationError(
            "at must be 'lhs', 'rhs', 'both' or occurrence indices, not %r"
            % (at,)
        )
    found = _equation(target)
    if found is None:
        if at == "both":
            return rewrite(target, p)
        raise DerivationError(
            "%r is not an equation, so has no %s" % (target, at)
        )
    A, a, b = found
    _, c, _ = endpoints(p)
    before, left, right = (occurrences(t, c) for t in (A, a, b))
    chosen = {
        "lhs": range(before, before + left),
        "rhs": range(before + left, before + left + right),
        "both": range(before, before + left + right),
    }[at]
    if not chosen:
        raise DerivationError(
            "%s does not occur in the %s of %s"
            % (
                c.repr_unicode(),
                {"lhs": "left side", "rhs": "right side"}.get(at, "equation"),
                target.repr_unicode(),
            )
        )
    return rewrite(target, p, list(chosen))


def _oriented(p: Judgement, start: Term, what: str) -> Judgement:
    """``p`` as an equation starting at ``start``, flipped if need be."""
    engine = p.engine
    _, c, d = endpoints(p)
    if engine.defeq(c, start):
        return p
    if engine.defeq(d, start):
        return symm(p)
    raise DerivationError(
        "%s relates %s and %s, neither of which is the %s %s"
        % (
            p.repr_unicode(),
            c.repr_unicode(),
            d.repr_unicode(),
            what,
            start.repr_unicode(),
        )
    )


def rhs_by(h: Judgement, p: Judgement) -> Judgement:
    """``a = b′`` from ``h : a = b`` and ``p`` between ``b`` and ``b′``."""
    _, _, b = endpoints(h)
    return trans(h, _oriented(p, b, "right side"))


def lhs_by(h: Judgement, p: Judgement) -> Judgement:
    """``a′ = b`` from ``h : a = b`` and ``p`` between ``a`` and ``a′``."""
    _, a, _ = endpoints(h)
    return trans(symm(_oriented(p, a, "left side")), h)


def assume(statement: Judgement, name: Optional[str] = None) -> Judgement:
    """A hypothesis of ``statement``, named ``h`` (primed until fresh) unless
    ``name`` is given: ``h = assume(x.eq(2 * y))``."""
    if name is None:
        (name,) = _fresh_names(["h"], (), set(statement.ctx.names()))
    return hyp(name, statement)


# -- axioms and imported statements ---------------------------------------------------


def axiom(
    name: str,
    statement: Judgement,
    provenance: Optional[Provenance] = None,
) -> Judgement:
    """Declare ``name`` as an inhabitant of ``statement`` without proof.

    This is how a theorem proved elsewhere -- in Lean 4, say -- is brought
    in: only the *statement* is translated, and the result is a constant
    with a typing rule, no definition and no computation rules. It is
    therefore typed, usable in derivations, and opaque to the evaluator.

    Hypotheses the statement depends on (set variables, families) become
    parameters of the declaration, so the axiom can be re-instantiated.

    Record where it came from in ``provenance``; ``Judgement.axioms`` and
    ``Judgement.trust_report`` then report it wherever it is used.
    """
    _require_set(statement)
    engine = statement.engine
    deps = _dependencies(statement)
    params, result = _schematise(statement, deps)
    arity = Arrow(cross(*[p.var.arity for p in params]), A0) if params else A0
    const = Const(name, arity)
    if const in engine.registry:
        raise DerivationError("%r is already declared" % (const,))
    engine.registry.axiom(const, Signature(tuple(params), result), provenance)
    args = tuple(entry.var for entry in deps)
    return Judgement(
        statement.ctx,
        const(*args) if args else const,
        statement.term,
        engine=engine,
        check=False,
        aliases=_aliases(statement),
    )


def _dependencies(statement: Judgement) -> Tuple[Param, ...]:
    """The context entries ``statement`` needs, transitively, in order."""
    needed = set(free_vars(statement.term))
    deps: List[Param] = []
    for entry in reversed(statement.ctx.entries):
        if entry.var not in needed:
            continue
        deps.append(entry)
        if entry.type is not None:
            needed |= free_vars(entry.type)
        for z, t in entry.hyps:
            needed |= free_vars(t)
            needed.discard(z)
    deps.reverse()
    return tuple(deps)


def _schematise(
    statement: Judgement, deps: Sequence[Param]
) -> Tuple[List[Param], Term]:
    """Turn the dependencies into signature parameters, renaming their
    variables to pattern variables so they cannot collide with a user's."""
    mapping: Dict[Var, Term] = {}
    params: List[Param] = []
    for entry in deps:
        local = dict(mapping)
        hyps = []
        for z, t in entry.hyps:
            pz = pvar(z.name, z.arity)
            hyps.append((pz, subst_many(t, local)))
            local[z] = pz
        assert entry.type is not None
        params.append(
            Param(
                pvar(entry.var.name, entry.var.arity),
                subst_many(entry.type, local),
                tuple(hyps),
            )
        )
        mapping[entry.var] = params[-1].var
    return params, subst_many(statement.term, mapping)


# -- identity ([BN] ch. 8) -----------------------------------------------------------


def refl(a: Judgement) -> Judgement:
    """Id-introduction: ``a ∈ A``  ⊢  ``refl(a) ∈ Id(A, a, a)``."""
    return Judgement(
        a.ctx,
        _refl(a.term),
        _Id(a.type, a.term, a.term),
        engine=a.engine,
        check=False,
        aliases=_aliases(a),
    )


def endpoints(p: Judgement) -> Tuple[Term, Term, Term]:
    """``(A, a, b)`` from ``p ∈ Id(A, a, b)``."""
    t = p.engine.whnf(p.type)
    if not (isinstance(t, App) and t.fn == _Id):
        raise DerivationError(
            "%r is not a proof of an identity: its type is %r" % (p, p.type)
        )
    return t.args[0], t.args[1], t.args[2]


def elim(
    p: Judgement, motive: Term, base: Term, type: Term, *inherit: Judgement
) -> Judgement:
    """``J(motive, p, base)`` with the conclusion type supplied by the rule."""
    ctx = merge(p.ctx, *[j.ctx for j in inherit])
    return Judgement(
        ctx,
        _J(motive, p.term, base),
        type,
        engine=p.engine,
        check=False,
        aliases=_aliases(p, *inherit),
    )


def symm(p: Judgement) -> Judgement:
    """``p ∈ Id(A, a, b)``  ⊢  ``symm(p) ∈ Id(A, b, a)``."""
    A, a, b = endpoints(p)
    return Judgement(
        p.ctx,
        _symm(A, a, b, p.term),
        _Id(A, b, a),
        engine=p.engine,
        check=False,
        aliases=_aliases(p),
    )


def trans(p: Judgement, q: Judgement) -> Judgement:
    """``p ∈ Id(A, a, b)``, ``q ∈ Id(A, b, c)``  ⊢  ``Id(A, a, c)``."""
    engine = p.engine
    A, a, b = endpoints(p)
    A2, b2, c = endpoints(q)
    if not engine.defeq(A, A2):
        raise DerivationError(
            "%r and %r are identities in different sets" % (p, q)
        )
    if not engine.defeq(b, b2):
        raise DerivationError(
            "%r ends at %r but %r starts at %r" % (p, b, q, b2)
        )
    return Judgement(
        merge(p.ctx, q.ctx),
        _trans(A, a, b, c, p.term, q.term),
        _Id(A, a, c),
        engine=engine,
        check=False,
        aliases=_aliases(p, q),
    )


def cong(f: Judgement, p: Judgement) -> Judgement:
    """``f ∈ A ⇒ B``, ``p ∈ Id(A, a, b)``  ⊢  ``Id(B, f(a), f(b))``.

    The proof is ``cong`` in the context ``(x) f(x)``.
    """
    engine = f.engine
    dom, fam = _expect_former(f, Pi, "a function")
    B = _constant_codomain(fam, f)
    A, a, b = endpoints(p)
    if not engine.defeq(dom, A):
        raise DerivationError("%r does not accept elements of %r" % (f, A))
    (x,) = _fresh(f, p, A, B, a, b)[:1]
    context = _abstract_term(_apply(f.term, x), [x])
    return Judgement(
        merge(p.ctx, f.ctx),
        _cong(A, B, a, b, context, p.term),
        _Id(B, _apply(f.term, a), _apply(f.term, b)),
        engine=engine,
        check=False,
        aliases=_aliases(p, f),
    )


Context_ = Union[Abs, Callable[[Judgement], object]]


def cong_in(context: Context_, p: Judgement) -> Judgement:
    """Congruence in a *term* context: ``p ∈ Id(A, a, b)`` gives
    ``Id(B, context(a), context(b))`` for a one-variable context.

    The context is an abstraction ``(x)t``, or a Python function from an
    element of ``A`` to a judgement, which is called on a fresh hypothesis
    and abstracted: ``cong_in(lambda t: t + 1, p)`` is the context
    ``(t)t + 1``. ``cong`` needs an element of ``A ⇒ B``; this needs no
    ``lam``. The codomain is inferred, which also checks the context is
    well typed.
    """
    engine = p.engine
    A, a, b = endpoints(p)
    abs_, ctx = _context(context, p, A)
    z = Var(
        _fresh_names(
            ["z"],
            (),
            set(ctx.names())
            | {v.name for v in free_vars(abs_) | free_vars(A)},
        )[0]
    )
    try:
        B = engine.checker.infer(ctx.extend(z, A), instantiate(abs_, [z]))
    except TypingError as error:
        raise DerivationError(
            "The context %r is not well typed over %r: %s" % (abs_, A, error)
        )
    if z in B:
        raise DerivationError(
            "The context %r has a dependent type; use transport instead"
            % (abs_,)
        )
    return Judgement(
        ctx,
        _cong(A, B, a, b, abs_, p.term),
        _Id(B, _at(abs_, a), _at(abs_, b)),
        engine=engine,
        check=False,
        aliases=_aliases(p),
    )


def _context(
    context: Context_, p: Judgement, A: Term
) -> Tuple[Abs, Context]:
    """A one-variable abstraction from ``context``, and the hypotheses the
    congruence over ``p`` depends on: ``p``'s and the context's own."""
    if isinstance(context, Abs):
        if len(context.arities) != 1:
            raise DerivationError(
                "%r is not a one-variable context" % (context,)
            )
        return context, p.ctx
    if isinstance(context, Judgement) or not callable(context):
        raise DerivationError(
            "%r is not a context: give an abstraction (x)t or a function"
            % (context,)
        )
    # the hole is a variable no user symbol can share, so a symbol the
    # function closes over is never captured; its name survives only as
    # the display hint, taken from the function's parameter
    code = getattr(context, "__code__", None)
    hint = code.co_varnames[0] if code is not None and code.co_argcount else "t"
    hole = Var("%s#%d" % (hint, next(_HOLES)))
    t = Judgement(
        p.ctx.extend(hole, A), hole, A, engine=p.engine, check=False
    )
    body = context(t)
    if not isinstance(body, Judgement):
        body = _side(body, t)  # type: ignore[arg-type]
    if body.is_set or body.is_family:
        raise DerivationError(
            "The context %r gives a set, not an element" % (context,)
        )
    ctx = merge(p.ctx, discharge(body.ctx, hole))
    return _abstract_term(body.term, [hole], hints=[hint]), ctx


_HOLES = itertools.count(1)


def transport(fam: Judgement, p: Judgement, c: Judgement) -> Judgement:
    """``P(z) set [z ∈ A]``, ``p ∈ Id(A, a, b)``, ``c ∈ P(a)``  ⊢  ``P(b)``.

    Substitution of equals for equals: a proof of a family at one endpoint
    is carried to the other.
    """
    engine = p.engine
    A, a, b = endpoints(p)
    if not (fam.is_family and len(fam.hyps) == 1):
        raise DerivationError("%r is not a family of one argument" % (fam,))
    if not engine.defeq(fam.hyps[0][1], A):
        raise DerivationError("%r is not a family over %r" % (fam, A))
    _expect_type(c, _at(fam.term, a))
    return _carry(fam.term, p, c, fam)


def _carry(
    family_term: Term, p: Judgement, c: Judgement, *inherit: Judgement
) -> Judgement:
    """``c ∈ P(a)`` carried along ``p ∈ Id(A, a, b)`` to ``P(b)``, as
    ``transport(p, c)``."""
    A, a, b = endpoints(p)
    return Judgement(
        merge(p.ctx, *[j.ctx for j in inherit], c.ctx),
        _transport(A, family_term, a, b, p.term, c.term),
        _at(family_term, b),
        engine=p.engine,
        check=False,
        aliases=_aliases(p, c, *inherit),
    )


# -- rewriting -----------------------------------------------------------------------


def occurrences(term: Term, pattern: Term) -> int:
    """How many times ``pattern`` occurs in ``term``.

    Occurrences are counted structurally (so up to alpha-equivalence) and
    are not searched inside one another.
    """
    count = 0

    def visit(t: Term, depth: int) -> Optional[Term]:
        nonlocal count
        if t == pattern:
            count += 1
            return t  # do not recurse into a match
        return None

    transform(term, visit)
    return count


def motive_for(
    term: Term, pattern: Term, var: Var, at: Optional[Sequence[int]] = None
) -> Abs:
    """``(var) term`` with occurrences of ``pattern`` replaced by ``var``.

    ``at`` selects which occurrences to abstract, by their zero-based index
    in reading order; the default is all of them.
    """
    wanted = None if at is None else set(at)
    seen = 0

    def visit(t: Term, depth: int) -> Optional[Term]:
        nonlocal seen
        if t == pattern:
            index = seen
            seen += 1
            if wanted is None or index in wanted:
                return var
            return t
        return None

    replaced = transform(term, visit)
    if wanted is not None:
        missing = sorted(i for i in wanted if i >= seen)
        if missing:
            raise DerivationError(
                "There %s only %d occurrence(s) of %r, so %s cannot be selected"
                % ("is" if seen == 1 else "are", seen, pattern, missing)
            )
    return _abstract_term(replaced, [var])


def rewrite(
    target: Judgement, p: Judgement, at: Optional[Sequence[int]] = None
) -> Judgement:
    """Rewrite ``target`` with the identity ``p``, left to right.

    ``target ∈ T`` and ``p ∈ Id(A, a, b)`` give a judgement of
    ``T[a := b]``, justified by transporting ``target`` along ``p``. Use
    ``p.symm`` to rewrite right to left, and ``at`` to pick which
    occurrences to rewrite (default: all).

    The motive built from ``T`` is checked to be a family over ``A``, so a
    rewrite that would be ill typed is refused rather than producing a
    judgement that does not hold.
    """
    engine = target.engine
    A, a, b = endpoints(p)
    if occurrences(target.type, a) == 0:
        raise DerivationError(
            "%r does not occur in %r, so there is nothing to rewrite" % (a, target.type)
        )
    z = Var(
        _fresh_names(
            ["z"],
            (),
            set(target.ctx.names())
            | set(p.ctx.names())
            | {v.name for v in free_vars(target.type) | free_vars(A)},
        )[0]
    )
    fam = motive_for(target.type, a, z, at)
    inner = merge(target.ctx, p.ctx).extend(z, A)
    try:
        engine.checker.is_set(inner, instantiate(fam, [z]))
    except TypingError as error:
        raise DerivationError(
            "Rewriting %r in %r is not type correct: %s" % (a, target.type, error)
        )
    return _carry(fam, p, target)


def _fresh(*parts: Union[Judgement, Term]) -> Tuple[Var, ...]:
    """Three fresh variables for a J motive, avoiding every name in ``parts``."""
    avoid = set()
    for part in parts:
        term = part.term if isinstance(part, Judgement) else part
        avoid |= {v.name for v in free_vars(term)}
        if isinstance(part, Judgement):
            avoid |= set(part.ctx.names())
    return tuple(Var(n) for n in _fresh_names(["x", "y", "z"], (), avoid))


# -- derivation trees ---------------------------------------------------------------


class Argument:
    """A step of a derivation: premises above the line, a conclusion below,
    optionally with discharged hypotheses and a rule label. Premises may be
    judgements or other arguments, so arguments nest into trees."""

    def __init__(
        self,
        premises: Iterable[Union[Judgement, "Argument"]] = (),
        conclusion: Optional[Judgement] = None,
        discharges: Iterable[Judgement] = (),
        label: str = "",
    ):
        if conclusion is None:
            raise DerivationError("An argument needs a conclusion")
        self.premises = tuple(premises)
        self.conclusion = conclusion
        self.discharges = tuple(discharges)
        self.label = label

    @property
    def leaves(self) -> Tuple[Judgement, ...]:
        """The undischarged judgements the tree rests on."""
        out: List[Judgement] = []
        for p in self.premises:
            out.extend(p.leaves if isinstance(p, Argument) else (p,))
        return tuple(out)

    def _renderer(self, style: str):
        from .render.text import TextRenderer

        aliases: dict = {}
        for j in self.leaves + (self.conclusion,):
            aliases.update(j.aliases)
        return TextRenderer(style, aliases)

    def repr_unicode(self) -> str:
        return self._renderer("unicode").render_argument(self)

    def repr_latex(self) -> str:
        return self._renderer("latex").render_argument(self)

    def __repr__(self) -> str:
        return self.repr_unicode()

    def _repr_latex_(self) -> str:
        """For Jupyter/IPython."""
        return "$$%s$$" % self.repr_latex()


# -- contexts -------------------------------------------------------------------------


def merge(*contexts: Context) -> Context:
    """The union of hypotheses, in order of first appearance; a variable
    assumed with two different types is an error."""
    entries: List[Param] = []
    seen = {}
    for ctx in contexts:
        for entry in ctx.entries:
            if entry.var in seen:
                if seen[entry.var] != entry:
                    raise DerivationError(
                        "%r is assumed with two different types: %r and %r"
                        % (entry.var, seen[entry.var].type, entry.type)
                    )
                continue
            seen[entry.var] = entry
            entries.append(entry)
    return Context(entries)


def discharge(ctx: Context, var: Var) -> Context:
    """Remove the hypothesis ``var``; nothing else may depend on it."""
    entries = []
    for entry in ctx.entries:
        if entry.var == var:
            continue
        mentioned = set()
        if entry.type is not None:
            mentioned |= free_vars(entry.type)
        for _, t in entry.hyps:
            mentioned |= free_vars(t)
        if var in mentioned:
            raise DerivationError(
                "Cannot discharge %r: the hypothesis %r depends on it"
                % (var, entry.var)
            )
        entries.append(entry)
    return Context(entries)


# -- helpers --------------------------------------------------------------------------


def _term_of(x: Union[Judgement, Term]) -> Term:
    return x.term if isinstance(x, Judgement) else x


def _aliases(*premises: Judgement) -> Dict[Term, str]:
    """Display aliases inherited from the premises of a rule."""
    out: Dict[Term, str] = {}
    for p in premises:
        out.update(p.aliases)
    return out


def _require_set(j: Judgement) -> None:
    if not isinstance(j, Judgement) or not j.is_set:
        raise DerivationError("%r is not a set" % (j,))


def _require_hypothesis(j: Judgement) -> None:
    if not isinstance(j, Judgement) or not j.is_hypothesis:
        raise DerivationError("%r is not a hypothesis" % (j,))


def _expect_type(j: Judgement, type: Term) -> None:
    if not j.engine.defeq(j.type, type):
        raise DerivationError("%r does not have type %r" % (j, type))


def _expect_former(j: Judgement, former: Const, what: str) -> Tuple[Term, Term]:
    """Unfold ``j``'s type to ``former(A, B)`` and return ``(A, B)``."""
    t = j.engine.whnf(j.type)
    if not (isinstance(t, App) and t.fn == former):
        raise DerivationError("%r is not %s: its type is %r" % (j, what, j.type))
    return t.args[0], t.args[1]


def _at(fam: Term, arg: Term) -> Term:
    """``B(a)`` for a family ``B``, beta-reduced when ``B`` is an abstraction."""
    if isinstance(fam, Abs):
        return instantiate(fam, [arg])
    return App(fam, (arg,))


def _applied(f: Term, arg: Term) -> Term:
    """``apply(f, arg)``, opening ``f`` when it is literally ``lam((x)b)``.

    A rule that has to feed arguments to a function the caller supplied
    should not leave a redex behind: a bare ``lam`` carries no domain, so
    ``apply(lam(b), a)`` is not re-checkable even though it is definitionally
    ``b(a)``. Opening it keeps the constructed proof term checkable. A
    function that is a variable or a constant is applied as usual.
    """
    if isinstance(f, App) and f.fn == _lam and isinstance(f.args[0], Abs):
        return instantiate(f.args[0], [arg])
    return _apply(f, arg)


def _constant_codomain(fam: Term, j: Judgement) -> Term:
    """The codomain of a non-dependent function type ``Π(A, (_)C)``."""
    if isinstance(fam, Abs):
        variables, body = open_abs(fam)
        if any(v in body for v in variables):
            raise DerivationError("%r has a dependent type; cases needs A ⇒ C" % (j,))
        return body
    raise DerivationError("%r has a dependent type; cases needs A ⇒ C" % (j,))


def _motive_from_step(f: Judgement) -> Term:
    """Read ``C`` off ``f ∈ ∀x.(C(x) ⇒ C(succ(x)))``."""
    dom, fam = _expect_former(f, Pi, "the step function ∀x.(C(x) ⇒ C(succ(x)))")
    if not f.engine.defeq(dom, N) or not isinstance(fam, Abs):
        raise DerivationError("%r is not a step function over N" % (f,))
    (x,), body = open_abs(fam)
    body = f.engine.whnf(body)
    if not (isinstance(body, App) and body.fn == Pi):
        raise DerivationError("%r is not a step function C(x) ⇒ C(succ(x))" % (f,))
    return _abstract_term(body.args[0], [x])
