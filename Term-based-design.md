# Term-based core: design

Design for the rewrite described in the README's *To Do*: replace the
class-per-operation expression hierarchy with a term datatype, a centralised
lazy evaluator and a type checker driven by declarations.

Status: **proposal**. Decisions already taken are listed first; everything else
is open to change.

## Decisions

| Question | Decision |
|---|---|
| Scope | New core package built alongside the existing `symbolize.expressions`. `symbolize.logic.typetheory` migrates first, using its current tests as the specification. `expressions` (integrals, groups, `Syntax.ipynb`) is untouched until parity, then becomes a facade or is retired. |
| Propositions | Martin-Löf: propositions *are* types. `∃` is `Σ`, the witness is extractable. No `Prop`, no proof irrelevance. See `Other-proof-engines.md` §1. |
| Arities | Kept. The term language *is* Nordström's theory of expressions ([BN] ch. 3): every term has an arity, and arity is checked at construction. Types (`a ∈ A`) are a second, separate discipline checked by the type checker. |
| Type formers | Declaration-driven. Each former is a data declaration (formation, constructors, eliminator, computation rules) in a registry. No Python class per operation. The declaration shape is chosen so a general inductive schema with generated recursors can be added later. |

## Problems being solved

From the README and from the work on `expression.py`:

1. **Eager evaluation.** `compute()` runs on construction and recurses through
   children; symbolic reductions loop or exhaust memory.
2. **Class-per-operation.** `succ`, `prim`, `fst`, `cases`, … each need a
   `ProofSymbol` subclass with `apply_proposition_type` and `compute`.
3. **Arity management** is scattered (`__arity__` on classes, `ArityArrow` checks
   in `apply`, `# TODO: is this correct?` on `exists`).
4. **Mutable expressions.** `replace` mutated `_assume_contains` in place;
   `parent` pointers are set in `__init__` and copied by `deepcopy`; equality
   depends on state.
5. **Binding is by name.** `contains_bind` walks parent pointers; substitution
   raises on any bound variable; `(x)f(x) ≠ (y)f(y)`.
6. **Families are faked.** `PropositionSymbol("C", assume_contains=[n])` stands in
   for a genuine family `C : 0 → 0`.
7. **Types stored on terms drift.** `proposition_type` is computed once and
   carried on the proof object; substitution has to remember to update it.

## Architecture

```
symbolize/terms/
    arity.py      A0, Arrow, Cross          (moved from expressions/arity.py, shared)
    term.py       Term ADT, smart constructors with arity checks
    binding.py    locally-nameless operations: open, close, instantiate, subst, free vars
    decl.py       Constant, Signature, TypeFormer, Definition, Registry
    eval.py       whnf, nf, defeq                (the centralised lazy evaluator)
    check.py      Context, Judgement, infer/check  (bidirectional type checker)
    derive.py     derivation-level operations: apply, abstract, pair, …, Argument
    render/       typestring, latex, unicode, graph visitors
    library/      pi.py sigma.py plus.py nat.py bool.py falsum.py logic.py
```

Dependency order is top to bottom: `term` knows nothing about types; `eval`
knows the registry but not the checker; `check` uses `eval`; `derive` is the
user-facing layer and the only one that constructs `Judgement`s.

## 1. Terms

Immutable, hashable, structurally compared. Frozen dataclasses (or `__slots__`
classes with `__eq__`/`__hash__` on the tuple of fields).

```
Term ::= Var(name, arity)               free variable (typed by a Context)
       | Bound(index)                   de Bruijn index into enclosing Abs
       | Const(name)                    reference to a registry entry (carries arity via registry)
       | App(fn, args: tuple[Term])     fn : α₁⊗…⊗αₙ → β,  args : αᵢ,  result β
       | Abs(n, body, hints)            (x₁…xₙ)body : α₁⊗…⊗αₙ → β;  hints are display names
       | Comb(items: tuple[Term])       e₁,…,eₙ : α₁⊗…⊗αₙ
       | Sel(term, i)                   (e).i : αᵢ
```

This is exactly [BN] §3.2–3.6: variables, constants, application, abstraction,
combination, selection. Binding is *only* by `Abs`; formers that bind (`Π`, `Σ`,
`λ`, `natrec`'s step case, …) take an `Abs` argument. So

```
forall(x, B)       today                →   Π(A, (x)B)       [BN] arity 0 ⊗ (0→0) → 0
p2.abstract(p1)    today                →   λ((x)b)          [BN] arity (0→0) → 0
```

### Arity as kind

`arity(t)` is total and cheap. Smart constructors (`mk_app`, `mk_abs`, …)
compute and check arities *once*, at construction; an ill-kinded term cannot be
built. This replaces the `check_arity` branches in `apply` and the
`warn("Skipping arity check")` path. `Var` carries its arity (a variable of
arity `0 → 0` is a family; this replaces `assume_contains`).

### Binders: locally nameless

Bound occurrences are `Bound(i)`; free variables are `Var`. Consequences:

- α-equivalence is structural equality: `(x)f(x) == (y)f(y)`.
- Substitution of a free variable can never capture; the
  "x is both free and bound" case that broke `contains_free` is not expressible.
- `contains_free(x)` is "does `Var x` occur", full stop. `contains_bind` and
  `parent` disappear.
- `general_bind_form()` disappears (it was α-normalisation by hand).

`binding.py` provides `abstract(term, [vars]) -> Abs` (close over free vars),
`instantiate(abs, [terms]) -> Term` (open with terms), `subst(term, var, t)`,
`free_vars(term)`. Renderers open binders with the `hints` names, freshened
against free variables in scope.

## 2. Declarations and the registry

Every non-variable head is a `Constant` in a `Registry`. The registry is the
single place a former's syntax, kind, typing and computation live.

```python
@dataclass(frozen=True)
class Constant:
    name: str
    arity: Arity
    notation: Notation           # prefix | infix(prec, assoc) | binder | quantifier | atom
    repr: Reprs                  # typestring / latex / unicode strings

@dataclass(frozen=True)
class Signature:
    """Schematic typing rule for App(const, args) — see §4."""
    params: tuple[Param, ...]    # one per argument, in order
    result: Term                 # type schema, may mention params

@dataclass(frozen=True)
class Rule:
    """Computation (ι/δ) rule: lhs pattern → rhs, both over pattern variables."""
    lhs: Term
    rhs: Term

@dataclass(frozen=True)
class TypeFormer:
    former: Constant             # e.g. Π
    formation: Signature         # premises for  Π(A, B) set
    constructors: tuple[tuple[Constant, Signature], ...]
    eliminators: tuple[tuple[Constant, Signature], ...]
    computation: tuple[Rule, ...]

@dataclass(frozen=True)
class Definition:
    const: Constant
    body: Abs                    # δ-unfolds to body applied to args
```

Registration is by module import (`library/nat.py` builds `N` and calls
`registry.add(N)`), mirroring today's `zero = …; succ = …` module constants.
Users can register their own formers the same way — no subclassing.

### Example: natural numbers ([BN] ch. 7, [ST] §4.7)

```python
N      = Constant("N",      A0,                                    …)
zero   = Constant("zero",   A0,                                    …)
succ   = Constant("succ",   Arrow(A0, A0),                         …)
natrec = Constant("natrec", Arrow(Cross(Arrow(A0,A0), A0, A0, Arrow(Cross(A0,A0),A0)), A0), …)
#                                  motive C,  n,  d,  e(x,y)

Nat = TypeFormer(
    former=N,
    formation=Signature(params=(), result=SET),
    constructors=(
        (zero, Signature(params=(),                result=N)),
        (succ, Signature(params=(Param("n", type=N),), result=N)),
    ),
    eliminators=(
        (natrec, Signature(
            params=(
                Param("C", arity=Arrow(A0, A0)),                          # motive; kind only
                Param("n", type=N),
                Param("d", type=C(zero)),
                Param("e", type=Π(N, (x) Π(C(x), (y) C(succ(x))))),
            ),
            result=C(n))),
    ),
    computation=(
        Rule(natrec(C, zero,    d, e),   d),
        Rule(natrec(C, succ(n), d, e),   e(n, natrec(C, n, d, e))),
    ),
)
```

Schemas (`C(zero)`, `C(n)`, rule sides) are ordinary terms over *pattern
variables* — `Var`s reserved for the declaration — so they are written with the
same constructors as user terms and rendered by the same renderers. This is a
near-verbatim transcription of the rule tables in [BN]/[ST], which is the point.

### Example: logic as definitions ([ST] ch. 4)

`⇒`, `∧`, `¬` are δ-definitions over `Π`, `Σ`, `⊥`; `∨` and `⊥` are primitive
formers (`+` and the empty type); `∀ ≡ Π`, `∃ ≡ Σ` are display aliases.

```python
implies = Definition(Constant("⟹", Arrow(Cross(A0, A0), A0), infix…),  (A, B) Π(A, (_) B))
and_    = Definition(Constant("∧", …),                                 (A, B) Σ(A, (_) B))
not_    = Definition(Constant("¬", Arrow(A0, A0), prefix…),            (A)    Π(A, (_) ⊥))
```

Renderers print the defined constant (`A ⟹ B`); the evaluator unfolds it only
when a rule needs to see the `Π` underneath. This gives the README's display
behaviour for free and removes `ImpliesPropositionExpression`,
`AndPropositionExpression`, … entirely.

### Schema-readiness

`constructors` is a list of `(Constant, Signature)` where each param has a type
— i.e. an inductive declaration. A later `inductive(...)` helper can *generate*
`eliminators` and `computation` from `constructors` (plus a positivity check)
and produce the same `TypeFormer`. Nothing in `eval` or `check` would change.

## 3. Evaluator

`eval.py` owns all computation. Nothing computes on construction.

- `whnf(t, fuel)` — reduce the head only, lazily:
  - β: `App(Abs(n, b), args) → instantiate(b, args)`
  - selection: `Sel(Comb(items), i) → items[i]`
  - η is handled in `defeq`, not by rewriting.
  - δ: `App(Const(d), args)` where `d` is a `Definition` → unfold.
  - ι: `App(Const(elim), args)` where `elim` is an eliminator → whnf the major
    premise(s) named by the rules, then try each `Rule.lhs` by first-order
    matching; on match return `instantiate(rhs)`.
  - otherwise stuck (variable-headed or constructor-headed): return as is.
- `nf(t, fuel)` — full normalisation, `whnf` then recurse into children.
- `defeq(a, b, fuel)` — `whnf` both, compare heads; recurse on children; η for
  `Abs` vs non-`Abs` by opening with a fresh variable.
- `fuel` is an explicit step budget; exhaustion raises `ReductionLimit` instead
  of blowing the Python stack. `whnf` is written as a loop, not recursion, on
  the spine.
- Memoisation: a per-call cache keyed on term hash (terms are immutable) for
  `whnf` and `defeq`. Optional hash-consing later if profiling says so.

`prim`'s `compute` in `natural.py` becomes two data rules and zero code; the
`addone` test in `test_examples.py` becomes `nf(addone(succ(zero)))`.

## 4. Type checker

Judgement forms ([BN] ch. 4): `A set`, `a ∈ A`, with hypotheses `Γ`.
Equality judgements are decided by `defeq`.

```python
Context   = tuple[tuple[Var, Term], ...]        # x ∈ A, ordered
Judgement = (ctx: Context, term: Term, type: Term)   # immutable; repr "x : A"
```

Bidirectional:

- `infer(Γ, t) -> Term`
  - `Var` → look up in Γ.
  - `App(Const(c), args)` → the constant's `Signature`: bind each `Param` to its
    argument (arity check), `check` each argument against its instantiated type
    schema, return the instantiated `result`.
  - `App(f, args)` with `f` not a constant → `infer f`, `whnf`, expect `Π(A, B)`
    (or a `Σ`/`+`/… pattern for that eliminator), `check args : A`, return `B(args)`.
  - `Sel`, `Comb` → component-wise.
  - bare `Abs` → **not inferable** (no domain annotation), as in [BN].
- `check(Γ, t, T)`
  - `Abs` against `Π(A, B)` → open with fresh `x ∈ A`, `check(body, B(x))`.
  - `Comb` against `Σ`… → component-wise.
  - otherwise `infer` and `defeq` against `T`.

Because `Abs` is not inferable, the *derivation* layer is where λ gets its type
(§5): abstracting `x ∈ A` out of `b ∈ B [x ∈ A]` yields `λ((x)b) ∈ Π(A, (x)B)`
by the Π-introduction rule, and the checker only ever re-checks that result.

### Motives

Dependent eliminators (`natrec`, `split` for Σ, `when` for `+`) take the motive
`C` as an explicit first argument (as `Nat.rec` does in Lean). This keeps the
`Signature` machinery first-order: every pattern variable in a schema is bound
directly to an argument, or to a sub-term of an argument's `whnf`'d type
matched against a constructor-headed pattern (`Π(A, B)`), so no higher-order
unification is needed.

The non-dependent conveniences used throughout [ST] — `fst`, `snd`, `cases`,
`ifthenelse`, `Fst`, `Snd` — are δ-definitions over the dependent eliminators
with a constant motive, e.g. `fst(p) := split(p, (_) A, (x, y) x)` where `A` is
read from `infer(p)`. The current `test_natural.test_natural_elimination` becomes

```python
n = Var("n", A0);  C = Var("C", Arrow(A0, A0))     # a genuine family
ctx = {n ∈ N, c ∈ C(zero), f ∈ Π(N, (x) Π(C(x), (y) C(succ(x))))}
infer(ctx, natrec(C, n, c, f))  ==  C(n)
```

### Types are derived, not stored

Terms carry no `proposition_type`. A `Judgement` pairs a term with its type and
context, and the type is produced by `infer`/`check` (cached on the judgement).
This is a deliberate deviation from the README's "each datum captures … its
proposition type": storing the type on the term is what made
`proposition_type` go stale under substitution, and it duplicates what the
checker knows. The user-visible object (`x : A`) is the judgement, so nothing is
lost.

## 5. Derivation layer (`derive.py`)

The natural-deduction API the README example uses, over judgements:

```python
A, B, C = (Var(s, A0) for s in "ABC")
x = hyp("x", A)                        # Judgement([x∈A], x, A)
a = hyp("a", implies(A, B))
ax = apply(a, x)                       # a(x) : B   [x∈A, a∈A⟹B]
lam = abstract(ax, x)                  # λ((x)a(x)) : A ⟹ B   [a∈A⟹B]   — x discharged
```

Each operation is one rule of [ST]: `apply` (⇒E/∀E), `abstract` (⇒I/∀I),
`pair` (∧I/∃I), `fst`/`snd`, `inl`/`inr`, `cases`, `natrec`, … It builds the
term with the smart constructors, computes the result type by the rule, and
returns a `Judgement` with the merged context. `Argument` (derivation trees for
LaTeX/HTML) moves here unchanged in spirit; its premises and conclusion are
judgements.

`P.get_proof("x")` survives as `hyp("x", P)`; a thin compatibility module can
keep the old names during migration.

## 6. Rendering

Visitors over the term ADT, one per target (typestring, LaTeX, unicode,
graph-tool). Notation comes from `Constant.notation`, so `∧` renders infix,
`Π`/`∀` as binders, `natrec` prefix — no `BinaryInfixExpression` subclasses.
Bound variables print from `Abs.hints`, freshened. Aliases (`.alias(name)`
today) become a render-time override table rather than state on the term.

## 7. Migration plan

Each milestone leaves the repository green.

| # | Milestone | Done when |
|---|---|---|
| 0 | This document agreed. | — |
| 1 | `terms/arity.py`, `term.py`, `binding.py`. | Unit tests: arity checks at construction; α-equivalence; substitution including the "x free and bound" case; `free_vars`. |
| 2 | `eval.py` with β/selection/δ, `whnf`/`nf`/`defeq`, fuel, cache. | Tests over hand-built terms; a deliberately looping definition raises `ReductionLimit`. |
| 3 | `decl.py` + `library/` for `Π Σ + ⊥ N Bool` and the logic definitions; ι-rules wired into `eval`. | `nf(addone(succ(zero)))`, `cases`/`ifthenelse` reductions; every rule in [ST] ch. 4 & §4.7 transcribed with a test. |
| 4 | `check.py` bidirectional checker, `Context`, `Judgement`. | `infer`/`check` tests for each rule; the `natrec` family example above. |
| 5 | `derive.py` + `Argument`; compatibility shim. | `tests/logic/typetheory/*` pass against the new core (ported or via shim). |
| 6 | `render/` parity. | README example and `Type Theory - Logic V2.ipynb` render identically. |
| 7 | Decide fate of `symbolize.expressions`. | Separate proposal. |

Milestone 3 may start with hand-coded `match` cases for `N` and `Bool` to get
`whnf` working end-to-end, then move them into the registry before the
milestone closes.

## Status and deviations (as built)

Milestones 1–6 are implemented in `symbolize/terms/`. Where the code differs
from the sections above:

- **Object-level `lam`/`apply`/`pair`** (`library/pi.py`, `sigma.py`) are the
  proof constructors, as in [BN]; meta-level `Abs`/`Comb` are only the
  binding and tupling syntax. Open question 4 is resolved: `Comb`/`Sel` stay,
  and `f((a, b))` normalises to `f(a, b)` at construction.
- **Hypothetical premises** in signatures (`Param.hyps`) express
  `e(x, y) ∈ C(succ(x)) [x ∈ N, y ∈ C(x)]` directly, so `natrec`, `split`
  and `when` follow the [BN] rule tables; `fst`/`snd`/`cases`/`ifthenelse`
  are the non-dependent [ST] forms as separate primitives.
- **Inference limits are by design**: `pair`, `inl`, `lam` and an applied `lam`
  have no inferable type. The derivation layer (`derive.py`) computes
  conclusion types from premise types rule by rule and does not re-infer
  composite proof terms; `judge(term, type)` runs the checker for terms that
  are checkable.
- **`Judgement` lives in `derive.py`**, not `check.py`; it carries an
  `Engine` (registry + evaluator + checker) so `run()`/`whnf()` need no
  arguments. Judgement equality includes the context.
- **Discharge is checked**: `abstract` refuses to bind a variable that an
  undischarged hypothesis depends on (the ∀I side condition), and allows a
  vacuous discharge.
- **Old spellings kept as aliases**: `get_proof` (= `hyp`), `.apply()`,
  `.select(i)`; `prim` (= `natrec` with the motive read off the step
  function). `Term` has `abstract`/`subst`/`free_vars`/`in` sugar.
- `decl.Registry` also records constructors and formers; `pvar("A")` makes
  pattern variables (`?A`) that cannot collide with user variables.
- **Rendering** (`render/`): notation is a table keyed by constant *name*
  (`render/notation.py`), registered by the library modules, so it is
  independent of the registry. One `TextRenderer` serves three styles:
  `typestring` is the faithful [BN] syntax (`⟹(A, B)`, `λ((x)b)`,
  `apply(f, a)`, `pair(a, b)`); `unicode`/`latex` are the pretty forms of the
  README and notebooks (`A ⟹ B`, `λ(x).b`, `f(a)`, `(a, b)`, `∀x.P(x)`).
  Binders are rendered by opening them with fresh variables, so display
  aliases (`p.fst.alias("fst~p")`) keyed by term keep matching under λ.
  Quantifier domains are not shown; a family `P` renders η-expanded as
  `∀x.P(x)`. `render/graph.py` gives DOT text and, if installed, a
  graph-tool graph. Argument trees render to `\frac{}{}` LaTeX and to a
  text tree; the old HTML table form was not ported.

## Non-goals (for this iteration)

- Universes (`Set ∈ Type`), and therefore polymorphic definitions. `SET` is a
  single built-in sort for formation judgements only.
- Identity type, lists, W-types — straightforward to add as declarations once
  the core exists.
- General inductive schema / recursor generation (§2 keeps the door open).
- `Prop` / proof irrelevance (see `Other-proof-engines.md`).
- Elaboration: implicit arguments, motive inference beyond the constant case,
  tactics.
- Symbolic algebra on the `expressions` side (groups, integrals, Gruntz).

## Open questions

1. Should `Var` carry its arity, or should arity live only in the context?
   Proposal above: on `Var`, since arity is a property of the *expression*
   in [BN], while type is a property of the *judgement*.
2. Explicit-motive syntax in the derivation layer: `natrec(C, n, d, e)` vs
   `natrec(n, d, e, motive=C)` with a constant-motive default.
3. Hash-consing terms from the start (cheap `is`-equality, shared caches) or
   only if profiling demands it.
4. Whether `Comb`/`Sel` are needed in the core at all, or only as the encoding
   of multi-argument application (`f(a, b) ≡ apply(f, (a, b))`) as in [BN].
   Keeping them matches the book; dropping them simplifies the checker.
5. Package name: `symbolize.terms` vs `symbolize.core`.

## References

* [BN] Nordström, Petersson, Smith — *Programming in Martin-Löf's Type Theory*,
  ch. 3 (expressions and arities), ch. 4 (judgements), ch. 7 (N), ch. 19–20
  (Π, Σ).
* [ST] Thompson — *Type Theory and Functional Programming*, ch. 4.
* `Other-proof-engines.md` — how these choices relate to Lean 4.
