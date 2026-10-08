"""Importing statements from Lean 4, and exporting them back for checking.

Only *statements* cross the boundary: a theorem's type is translated into a
symbolize set, and declared as an axiom (a constant with a signature, no
definition, no computation rules). The proof term is never translated -- see
``AGENTS.md`` §1, "Where theorems come from".

The translation of the statement is therefore the trusted step, and this
module is deliberately strict: anything it does not understand is refused
with a message naming the problem, rather than guessed at. In particular
Lean's ``Exists`` is refused, because it is proof-irrelevant with no large
elimination while symbolize's ``exists`` is a strong sigma -- mapping one to
the other would hand back a witness the source never proved existed.

``Eq`` *is* mapped to ``Id``, which does give it computational content it
lacks in Lean. That is sound here: an imported proof is an opaque constant,
so ``J`` applied to it is stuck and no computation can depend on its
internals.

Input format
------------
A Lean ``Expr`` serialised as JSON, one object per node::

    {"kind": "const",   "name": "Nat.add", "levels": []}
    {"kind": "app",     "fn": <expr>, "arg": <expr>}
    {"kind": "forallE", "binderName": "n", "binderType": <expr>, "body": <expr>}
    {"kind": "lam",     "binderName": "x", "binderType": <expr>, "body": <expr>}
    {"kind": "bvar",    "index": 0}
    {"kind": "sort",    "level": "0"}
    {"kind": "lit",     "natVal": 2}
    {"kind": "mdata",   "expr": <expr>}
    {"kind": "letE",    "type": <expr>, "value": <expr>, "body": <expr>}

``Export.lean`` in this directory produces that shape. De Bruijn indices are
used as Lean uses them, which is also how ``Bound`` works here.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from ..arity import A0
from ..binding import instantiate, transform
from ..decl import SET, Provenance
from ..derive import Engine, Judgement, axiom, judge
from ..library import (
    Bool,
    Falsum,
    Id,
    N,
    add,
    and_,
    apply,
    false,
    implies,
    lam,
    mul,
    not_,
    numeral,
    or_,
    refl,
    succ,
    true,
    zero,
)
from ..term import Abs, App, Bound, Const, Term, TermError

Builder = Callable[[Sequence[Any], "LeanImporter"], Term]


class LeanImportError(TermError):
    """A Lean statement could not be translated faithfully."""


class LeanExportError(TermError):
    """A symbolize term has no Lean rendering, so it cannot be round-tripped."""


@dataclass(frozen=True)
class Rule:
    """How one Lean constant becomes a symbolize term.

    ``arity`` is the exact number of arguments the Lean application must
    carry, implicit and instance arguments included. Then either ``refuse``
    explains why the constant must not be imported, or ``build`` constructs
    the term, or ``head`` is applied to the arguments named by ``keep`` (an
    empty ``head`` with a single ``keep`` passes that argument through,
    which is how instance wrappers such as ``OfNat.ofNat`` are dropped).
    """

    arity: int
    head: Optional[Term] = None
    keep: Tuple[int, ...] = ()
    build: Optional[Builder] = None
    refuse: str = ""
    exact: bool = True

    def __post_init__(self) -> None:
        if self.refuse or self.build is not None:
            return
        if self.head is None and len(self.keep) != 1:
            raise ValueError("a pass-through rule keeps exactly one argument")
        for i in self.keep:
            if not 0 <= i < self.arity:
                raise ValueError("keep index %d is outside the arity" % i)


def _iff(args: Sequence[Any], importer: "LeanImporter") -> Term:
    left, right = importer.term(args[0]), importer.term(args[1])
    return and_(implies(left, right), implies(right, left))


#: The constants understood by default. Extend it with ``LeanImporter(rules=...)``.
STANDARD_RULES: Dict[str, Rule] = {
    # naturals
    "Nat": Rule(0, head=N),
    "Nat.zero": Rule(0, head=zero),
    "Nat.succ": Rule(1, head=succ, keep=(0,)),
    "Nat.add": Rule(2, head=add, keep=(0, 1)),
    "Nat.mul": Rule(2, head=mul, keep=(0, 1)),
    # the bundled operators, dropping the type and instance arguments
    "HAdd.hAdd": Rule(6, head=add, keep=(4, 5)),
    "HMul.hMul": Rule(6, head=mul, keep=(4, 5)),
    "OfNat.ofNat": Rule(3, keep=(1,)),
    # equality
    "Eq": Rule(3, head=Id, keep=(0, 1, 2)),
    "Eq.refl": Rule(2, head=refl, keep=(1,)),
    "rfl": Rule(2, head=refl, keep=(1,)),
    # propositional connectives
    "And": Rule(2, head=and_, keep=(0, 1)),
    "Or": Rule(2, head=or_, keep=(0, 1)),
    "Not": Rule(1, head=not_, keep=(0,)),
    "False": Rule(0, head=Falsum),
    # booleans (the datatype, not Prop)
    "Bool": Rule(0, head=Bool),
    "Bool.true": Rule(0, head=true),
    "Bool.false": Rule(0, head=false),
    # refusals: each of these would be unsound, junk-valued, or unstatable
    "Exists": Rule(
        2,
        refuse=(
            "Lean's Exists is proof-irrelevant and forbids large elimination, "
            "while symbolize's exists is a strong sigma whose witness is "
            "extractable. Restate the source with Sigma or PSigma, or import "
            "the statement under a different, opaque existential"
        ),
    ),
    "Iff": Rule(
        2,
        build=_iff,
        exact=False,
        refuse=(
            "Lean's Iff is a structure, so the conjunction of implications "
            "this would translate to is not definitionally equal to it and "
            "cannot be round-trip checked. State the source as a conjunction "
            "of implications, or add Iff to a custom rule table accepting that"
        ),
    ),
    "True": Rule(0, refuse="there is no unit set in the library to map True onto"),
    "Nat.sub": Rule(
        2,
        refuse=(
            "Nat.sub truncates at zero in Lean, so a statement about it is "
            "not a statement about subtraction; add it to a custom rule table "
            "only alongside a truncating definition here"
        ),
    ),
    "HDiv.hDiv": Rule(
        6,
        refuse=(
            "division is junk-valued at zero in Lean (x / 0 = 0); import such "
            "a statement only with a matching definition here"
        ),
    ),
    "Classical.em": Rule(
        1,
        refuse=(
            "classical reasoning has no counterpart in this intuitionistic " "theory"
        ),
    ),
    "Classical.choice": Rule(1, refuse="choice has no counterpart here"),
}


class LeanImporter:
    """Translates Lean statements into symbolize sets and declares them."""

    def __init__(
        self,
        engine: Engine,
        rules: Optional[Mapping[str, Rule]] = None,
        system: str = "lean4",
        version: str = "",
    ):
        self.engine = engine
        self.rules: Dict[str, Rule] = dict(STANDARD_RULES)
        if rules:
            self.rules.update(rules)
        self.system = system
        self.version = version

    # -- translation -----------------------------------------------------------

    def term(self, expr: Any) -> Term:
        """Translate one Lean ``Expr`` node into a term."""
        if not isinstance(expr, dict):
            raise LeanImportError("Expected an Expr object, got %r" % (expr,))
        kind = expr.get("kind")
        handler = getattr(self, "_kind_" + str(kind), None)
        if handler is None:
            raise LeanImportError("Unsupported Expr kind %r" % (kind,))
        return handler(expr)

    def statement(self, expr: Any) -> Judgement:
        """Translate a theorem's type and check that it really is a set.

        The check is what catches a translation that is merely well formed
        rather than meaningful.
        """
        return judge(self.term(expr), SET, engine=self.engine)

    def theorem(
        self,
        expr: Any,
        name: str,
        lean_name: str = "",
        statement: str = "",
        note: str = "",
    ) -> Judgement:
        """Translate a theorem's type and declare it as an axiom."""
        provenance = Provenance(
            system=self.system,
            version=self.version,
            name=lean_name or name,
            statement=statement,
            note=note,
        )
        return axiom(name, self.statement(expr), provenance)

    def load(self, source: str) -> Dict[str, Judgement]:
        """Import every theorem in a JSON export.

        The export is ``{"version": ..., "declarations": [{"name": ...,
        "type": <expr>, "statement": "..."}, ...]}``; a declaration may give
        ``symbolizeName`` to be declared under a different name here.
        """
        data = json.loads(source)
        if self.version == "" and isinstance(data.get("version"), str):
            self.version = data["version"]
        out: Dict[str, Judgement] = {}
        for entry in data.get("declarations", ()):
            lean_name = entry["name"]
            local = entry.get("symbolizeName") or lean_name.replace(".", "_")
            out[local] = self.theorem(
                entry["type"],
                local,
                lean_name=lean_name,
                statement=entry.get("statement", ""),
            )
        return out

    # -- one handler per Expr kind ---------------------------------------------

    def _kind_bvar(self, expr: Any) -> Term:
        index = expr.get("index")
        if not isinstance(index, int) or index < 0:
            raise LeanImportError("Bad de Bruijn index %r" % (index,))
        return Bound(index)

    def _kind_mdata(self, expr: Any) -> Term:
        return self.term(expr["expr"])

    def _kind_const(self, expr: Any) -> Term:
        return self._apply_rule(expr["name"], ())

    def _kind_lit(self, expr: Any) -> Term:
        if "natVal" in expr:
            value = expr["natVal"]
            if not isinstance(value, int) or value < 0:
                raise LeanImportError("Bad natural literal %r" % (value,))
            return numeral(value)
        raise LeanImportError(
            "Only natural number literals can be imported, not %r" % (expr,)
        )

    def _kind_sort(self, expr: Any) -> Term:
        raise LeanImportError(
            "A sort (%s) appears in the statement: there are no universes "
            "here, so a universe-polymorphic statement cannot be imported. "
            "Import a monomorphic instance instead" % (expr.get("level", "?"),)
        )

    def _kind_fvar(self, expr: Any) -> Term:
        raise LeanImportError(
            "The statement is not closed: it mentions the free variable %r"
            % (expr.get("name"),)
        )

    def _kind_mvar(self, expr: Any) -> Term:
        raise LeanImportError("The statement contains an unassigned metavariable")

    def _kind_proj(self, expr: Any) -> Term:
        raise LeanImportError(
            "Structure projection (%s.%s) cannot be imported: there are no "
            "structures in the library" % (expr.get("structName"), expr.get("idx"))
        )

    def _kind_forallE(self, expr: Any) -> Term:
        domain = self.term(expr["binderType"])
        body = self.term(expr["body"])
        hint = expr.get("binderName") or "x"
        without = _drop_binder(body)
        if without is not None:  # the binder is unused: an implication
            return implies(domain, without)
        return _forall(domain, Abs((A0,), body, hints=(hint,)))

    def _kind_lam(self, expr: Any) -> Term:
        self.term(expr["binderType"])  # translated to surface any refusal
        body = self.term(expr["body"])
        hint = expr.get("binderName") or "x"
        return lam(Abs((A0,), body, hints=(hint,)))

    def _kind_letE(self, expr: Any) -> Term:
        value = self.term(expr["value"])
        body = self.term(expr["body"])
        return instantiate(Abs((A0,), body), [value])

    def _kind_app(self, expr: Any) -> Term:
        head, args = _spine(expr)
        if head.get("kind") == "const":
            return self._apply_rule(head["name"], args)
        result = self.term(head)
        for arg in args:
            result = apply(result, self.term(arg))
        return result

    # -- rules ------------------------------------------------------------------

    def _apply_rule(self, name: str, args: Sequence[Any]) -> Term:
        rule = self.rules.get(name)
        if rule is None:
            raise LeanImportError(
                "No rule for the Lean constant %r. Add one to the rule table, "
                "mapping it to a symbolize term of the same meaning" % (name,)
            )
        if rule.refuse:
            raise LeanImportError("%r cannot be imported: %s" % (name, rule.refuse))
        if len(args) != rule.arity:
            raise LeanImportError(
                "%r takes %d argument(s) here but the statement applies it to "
                "%d; partial or over-application is not supported"
                % (name, rule.arity, len(args))
            )
        if rule.build is not None:
            return rule.build(args, self)
        kept = [self.term(args[i]) for i in rule.keep]
        if rule.head is None:
            return kept[0]
        if not kept:
            return rule.head
        return rule.head(*kept)


def _spine(expr: Any) -> Tuple[Any, List[Any]]:
    """Split a curried Lean application into its head and arguments."""
    args: List[Any] = []
    while isinstance(expr, dict) and expr.get("kind") in ("app", "mdata"):
        if expr["kind"] == "mdata":
            expr = expr["expr"]
            continue
        args.append(expr["arg"])
        expr = expr["fn"]
    args.reverse()
    return expr, args


def _drop_binder(body: Term) -> Optional[Term]:
    """``body`` shifted out from under one binder, or None if it uses it."""
    used = False

    def shift(t: Term, depth: int) -> Optional[Term]:
        nonlocal used
        if isinstance(t, Bound):
            i = t.index - depth
            if i == 0:
                used = True
                return t
            if i > 0:
                return Bound(t.index - 1, t.arity)
        return None

    shifted = transform(body, shift)
    return None if used else shifted


def _forall(domain: Term, body: Abs) -> Term:
    from ..library import forall

    return forall(domain, body)


# -- export, for round-trip checking -------------------------------------------------

#: How each symbolize constant is written in Lean.
LEAN_NAMES: Dict[str, str] = {
    "N": "Nat",
    "0": "Nat.zero",
    "succ": "Nat.succ",
    "add": "Nat.add",
    "mul": "Nat.mul",
    "∧": "And",
    "∨": "Or",
    "¬": "Not",
    "⊥": "False",
    "Bool": "Bool",
    "True": "Bool.true",
    "False": "Bool.false",
}


def to_lean(term: Term) -> str:
    """Render ``term`` as Lean 4 source.

    Only the statement language is covered; proof terms and the eliminators
    raise, because a round trip only ever needs the statement.
    """
    return _to_lean(term, [])


def _to_lean(t: Term, names: List[str]) -> str:
    from ..library import Id, exists, forall, implies, lam, refl

    if isinstance(t, Bound):
        if t.index < len(names):
            return names[t.index]
        raise LeanExportError("A bound variable escapes its binder")
    if isinstance(t, Const):
        lean = LEAN_NAMES.get(t.name)
        if lean is None:
            raise LeanExportError(
                "No Lean name for the constant %r, so this statement cannot "
                "be round-tripped" % (t.name,)
            )
        return lean
    if isinstance(t, Abs):
        raise LeanExportError("A bare abstraction has no Lean rendering")
    if isinstance(t, App) and isinstance(t.fn, Const):
        head, args = t.fn, t.args
        if head == Id and len(args) == 3:
            return "(@Eq %s %s %s)" % tuple(_to_lean(a, names) for a in args)
        if head == refl and len(args) == 1:
            return "(Eq.refl %s)" % _to_lean(args[0], names)
        if head == implies and len(args) == 2:
            return "(%s → %s)" % (
                _to_lean(args[0], names),
                _to_lean(args[1], names),
            )
        if head in (forall, exists) and len(args) == 2:
            if head == exists:
                raise LeanExportError(
                    "symbolize's strong existential has no faithful Lean "
                    "rendering; see the note on Exists above"
                )
            return _to_lean_binder("∀", args[0], args[1], names)
        if head == lam and len(args) == 1 and isinstance(args[0], Abs):
            return _to_lean_binder("fun", None, args[0], names, arrow=" => ")
        if head.name == "apply" and len(args) == 2:
            return "(%s %s)" % (
                _to_lean(args[0], names),
                _to_lean(args[1], names),
            )
        rendered = _to_lean(head, names)
        return "(%s %s)" % (
            rendered,
            " ".join(_to_lean(a, names) for a in args),
        )
    if isinstance(t, App):
        return "(%s %s)" % (
            _to_lean(t.fn, names),
            " ".join(_to_lean(a, names) for a in t.args),
        )
    raise LeanExportError("No Lean rendering for %r" % (t,))


def _to_lean_binder(
    keyword: str,
    domain: Optional[Term],
    body: Term,
    names: List[str],
    arrow: str = ", ",
) -> str:
    if not isinstance(body, Abs) or len(body.arities) != 1:
        raise LeanExportError("Expected a one-variable abstraction, got %r" % (body,))
    name = _fresh(body.hints[0], names)
    inner = _to_lean(body.body, [name] + names)
    if domain is None:
        return "(%s %s%s%s)" % (keyword, name, arrow, inner)
    return "(%s (%s : %s)%s%s)" % (
        keyword,
        name,
        _to_lean(domain, names),
        arrow,
        inner,
    )


def _fresh(hint: str, taken: Sequence[str]) -> str:
    name = hint or "x"
    while name in taken:
        name += "'"
    return name


@dataclass(frozen=True)
class RoundTrip:
    """A Lean snippet asserting that a translation is faithful.

    Lean accepts ``example : <translated> := <original>`` exactly when the
    translated statement is definitionally equal to the original theorem's
    type, which is the strongest check available without translating proofs.
    """

    local_name: str
    lean_name: str
    statement: str
    exact: bool = True

    def __str__(self) -> str:
        head = "-- %s  (imported as %s)" % (self.lean_name, self.local_name)
        if not self.exact:
            return (
                "%s\n-- NOT definitionally equal; check by hand:\n-- example : %s := %s"
                % (
                    head,
                    self.statement,
                    self.lean_name,
                )
            )
        return "%s\nexample : %s := %s" % (head, self.statement, self.lean_name)


def round_trip(judgement: Judgement, lean_name: str, exact: bool = True) -> RoundTrip:
    """The round-trip check for one imported judgement."""
    record = judgement.engine.registry.provenance(_axiom_const(judgement))
    return RoundTrip(
        local_name=_axiom_const(judgement).name,
        lean_name=lean_name or (record.name if record else ""),
        statement=to_lean(judgement.type),
        exact=exact,
    )


def _axiom_const(judgement: Judgement) -> Const:
    used = judgement.axioms
    if len(used) != 1:
        raise LeanExportError(
            "Expected a judgement resting on exactly one axiom, found %d" % len(used)
        )
    return used[0]


def round_trip_file(
    checks: Sequence[RoundTrip], imports: Sequence[str] = ("Init",)
) -> str:
    """A complete Lean file verifying every translation in ``checks``.

    Run it with your own toolchain: if it compiles, each statement is
    definitionally equal to the theorem it claims to import.
    """
    lines = [
        "-- Generated by symbolize: round-trip check of imported statements.",
        "-- If this file compiles, every translation below is definitionally",
        "-- equal to the Lean theorem it was imported from.",
        "",
    ]
    lines += ["import %s" % name for name in imports]
    lines.append("")
    for check in checks:
        lines.append(str(check))
        lines.append("")
    return "\n".join(lines)
