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

from typing import Dict, Iterable, List, Optional, Sequence, Tuple, Union

from .arity import A0, Arrow, cross
from .binding import abstract as _abstract_term
from .binding import free_vars, instantiate, open_abs, subst
from .check import Checker, Context
from .decl import SET, Param, Registry
from .eval import Evaluator
from .library import STANDARD, Bool, Falsum, N, Pi, Plus, Sigma
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
from .library import not_ as _not
from .library import or_ as _or
from .library import pair as _pair
from .library import snd as _snd
from .library import succ, zero
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

    def subst(self, var: "Judgement", value: "Judgement") -> "Judgement":
        return substitute(self, var, value)

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

    # -- spellings from the previous API -------------------------------------

    get_proof = hyp

    def apply(self, *args: "Judgement") -> "Judgement":
        return self(*args)

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
    step = _apply(_apply(f.term, x), y).abstract(x, y)
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
