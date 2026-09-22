"""Text renderers: typestring (the faithful [BN] syntax), unicode and LaTeX
(the pretty forms), for terms, judgements and derivation trees.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Sequence, Set, Tuple

from ..binding import free_vars, instantiate
from ..term import Abs, App, Bound, Comb, Const, Sel, Term, Var, _fresh_names
from .notation import APPLY, BINDER, INFIX, PREFIX, QUANTIFIER, TUPLE, lookup

if TYPE_CHECKING:
    from ..check import Context
    from ..derive import Argument, Judgement


class TextRenderer:
    """Render terms in one of the styles ``typestring``, ``unicode``, ``latex``.

    ``aliases`` maps terms to display names (``p.alias("fst~p")``).
    """

    def __init__(
        self, style: str = "unicode", aliases: Optional[Dict[Term, str]] = None
    ):
        if style not in ("typestring", "unicode", "latex"):
            raise ValueError("Unknown rendering style %r" % style)
        self.style = style
        self.aliases: Dict[Term, str] = dict(aliases or {})
        self.faithful = style == "typestring"

    # -- terms ----------------------------------------------------------------------

    def render(self, term: Term) -> str:
        return self._render(term, set())

    def _symbol(self, const: Const) -> str:
        return lookup(const).symbol(self.style, const.name)

    def _kind(self, term: Term) -> str:
        """The notation kind of an application's head (prefix if faithful)."""
        if isinstance(term, App) and isinstance(term.fn, Const):
            return PREFIX if self.faithful else lookup(term.fn).kind
        return PREFIX

    def _render(self, t: Term, scope: Set[str]) -> str:
        """Render ``t``; ``scope`` holds the names of enclosing binders.

        Binders are opened with fresh variables named after their hints, so
        subterms are always locally closed and aliases keyed by term match
        under binders too.
        """
        if t in self.aliases:
            return self.aliases[t]
        if isinstance(t, Var):
            return t.name
        if isinstance(t, Const):
            return self._symbol(t)
        if isinstance(t, Bound):
            return "#%d" % t.index  # only in an abstraction that was not opened
        if isinstance(t, Abs):
            inner, body, scope = self._open(t, scope)
            return "(%s)%s" % (
                ", ".join(inner),
                self._wrap(body, self._render(body, scope), ("abs",)),
            )
        if isinstance(t, Comb):
            return ", ".join(self._render(i, scope) for i in t.items)
        if isinstance(t, Sel):
            return "(%s).%d" % (self._render(t.term, scope), t.index)
        if isinstance(t, App):
            return self._render_app(t, scope)
        raise TypeError("Cannot render %r" % (t,))

    def _open(self, t: Abs, scope: Set[str]) -> Tuple[Tuple[str, ...], Term, Set[str]]:
        """Fresh names for the binder, the opened body, and the inner scope."""
        avoid = {v.name for v in free_vars(t.body)} | scope
        inner = _fresh_names(t.hints, (), avoid)
        variables = [Var(n, a) for n, a in zip(inner, t.arities)]
        return inner, instantiate(t, variables), scope | set(inner)

    def _render_app(self, t: App, scope: Set[str]) -> str:
        args = t.args
        if isinstance(t.fn, Const):
            note = lookup(t.fn)
            kind = PREFIX if self.faithful else note.kind
            sym = self._symbol(t.fn)
            if kind == INFIX and len(args) == 2:
                return "%s %s %s" % (
                    self._operand(args[0], scope),
                    sym,
                    self._operand(args[1], scope),
                )
            if kind == QUANTIFIER and len(args) == 2:
                return self._quantifier(sym, args[1], scope)
            if kind == BINDER and len(args) == 1 and isinstance(args[0], Abs):
                return self._binder(sym, args[0], scope)
            if kind == APPLY and len(args) == 2:
                head = self._render(args[0], scope)
                if self._kind(args[0]) in (BINDER, INFIX, QUANTIFIER):
                    head = "(%s)" % head
                return "%s(%s)" % (head, self._render(args[1], scope))
            if kind == TUPLE:
                return "(%s)" % ", ".join(self._render(a, scope) for a in args)
            head = sym
        else:
            head = self._render(t.fn, scope)
            if isinstance(t.fn, Abs):
                head = "(%s)" % head
        return "%s(%s)" % (head, ", ".join(self._render(a, scope) for a in args))

    def _operand(self, t: Term, scope: Set[str]) -> str:
        """An operand of an infix connective, parenthesised if compound."""
        s = self._render(t, scope)
        if self._kind(t) in (INFIX, QUANTIFIER, BINDER) or isinstance(t, Abs):
            return "(%s)" % s
        return s

    def _quantifier(self, sym: str, body: Term, scope: Set[str]) -> str:
        """``∀x.B`` from ``∀(A, (x)B)``; a family ``P`` is shown as ``∀x.P(x)``."""
        if isinstance(body, Abs):
            inner, opened, inner_scope = self._open(body, scope)
            wrapped = self._wrap(opened, self._render(opened, inner_scope), (INFIX,))
        else:
            avoid = {v.name for v in free_vars(body)} | scope
            inner = _fresh_names(["x"], (), avoid)
            wrapped = "%s(%s)" % (self._render(body, scope), inner[0])
        if self.style == "latex":
            return "%s{%s}.%s" % (sym, ", ".join(inner), wrapped)
        return "%s%s.%s" % (sym, ", ".join(inner), wrapped)

    def _binder(self, sym: str, body: Abs, scope: Set[str]) -> str:
        """``λx.b``; an application body is parenthesised, a nested binder
        is not (``λ(a).λ(b).λ(x).(b(a(x)))``)."""
        inner, opened, inner_scope = self._open(body, scope)
        rendered = self._render(opened, inner_scope)
        if isinstance(opened, App) and self._kind(opened) not in (
            BINDER,
            QUANTIFIER,
            TUPLE,
        ):
            rendered = "(%s)" % rendered
        if self.style == "latex":
            return "%s{}(%s).%s" % (sym, ", ".join(inner), rendered)
        return "%s(%s).%s" % (sym, ", ".join(inner), rendered)

    def _wrap(self, t: Term, rendered: str, when: Sequence[str]) -> str:
        """Parenthesise ``rendered`` (of ``t``) if its shape is in ``when``:
        notation kinds, ``"app"`` (any application), ``"abs"``."""
        if "app" in when and isinstance(t, App):
            return "(%s)" % rendered
        if "abs" in when and isinstance(t, Abs):
            return "(%s)" % rendered
        if self._kind(t) in when:
            return "(%s)" % rendered
        return rendered

    # -- judgements and derivations ------------------------------------------------------

    def render_judgement(self, j: "Judgement") -> str:
        if j.is_family:
            args = ", ".join(x.name for x, _ in j.hyps)
            return "%s(%s)" % (self.render(j.term), args)
        if j.is_set:
            return self.render(j.term)
        return "%s : %s" % (self.render(j.term), self.render(j.type))

    def render_context(self, ctx: "Context") -> str:
        parts = []
        for entry in ctx.entries:
            if entry.type is None:
                continue
            if entry.hyps:
                args = ", ".join(x.name for x, _ in entry.hyps)
                parts.append("%s(%s)" % (self.render(entry.var), args))
            else:
                parts.append(
                    "%s : %s" % (self.render(entry.var), self.render(entry.type))
                )
        return "[%s]" % ", ".join(parts)

    def render_argument(self, arg: "Argument") -> str:
        from ..derive import Argument

        if self.style == "latex":
            return self._argument_latex(arg)
        lines = []
        for p in arg.premises:
            lines.append(
                self.render_argument(p)
                if isinstance(p, Argument)
                else self.render_judgement(p)
            )
        top = "   ".join(lines)
        if arg.discharges:
            top = "[%s] ⋮ %s" % (
                ", ".join(self.render_judgement(d) for d in arg.discharges),
                top,
            )
        bottom = self.render_judgement(arg.conclusion)
        label = " (%s)" % arg.label if arg.label else ""
        width = max(len(top), len(bottom))
        return "%s\n%s%s\n%s" % (top, "-" * width, label, bottom)

    def _argument_latex(self, arg: "Argument") -> str:
        from ..derive import Argument

        top = r" \quad ".join(
            (
                self._argument_latex(p)
                if isinstance(p, Argument)
                else self.render_judgement(p)
            )
            for p in arg.premises
        )
        if arg.discharges:
            top = r"\begin{matrix}[%s]\\ \vdots\\ %s\\ \end{matrix}" % (
                r" \quad ".join(self.render_judgement(d) for d in arg.discharges),
                top,
            )
        label = "(%s)" % arg.label if arg.label else ""
        return r"\frac{%s}{%s}%s" % (top, self.render_judgement(arg.conclusion), label)


def typestring(term: Term, **kw) -> str:
    return TextRenderer("typestring", **kw).render(term)


def unicode(term: Term, **kw) -> str:
    return TextRenderer("unicode", **kw).render(term)


def latex(term: Term, **kw) -> str:
    return TextRenderer("latex", **kw).render(term)
