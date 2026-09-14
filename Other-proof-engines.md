# Symbolize and other proof engines

Notes on how the type theory implemented in `symbolize` relates to the design of
established proof assistants, in particular Lean 4. Written to inform the
term-based / centralised-evaluator rewrite described in the README's *To Do*.

## Lineage

`symbolize` follows Nordström *et al.* ([BN]) and Thompson ([ST]), i.e.
Martin-Löf intensional type theory (ITT). Lean 4's kernel implements a variant of
the Calculus of Inductive Constructions (CIC), which is a descendant of the same
ideas: dependent function types (Π), propositions-as-types, an intensional
identity type, inductive types, and computation by reduction.

The two are therefore **not incompatible**; they are members of the same family.
The rewrite planned in the README — a term datatype plus a central lazy
evaluator — is essentially the shape of Lean's `Expr` type together with its
kernel `whnf` / `isDefEq` routines. That redesign moves `symbolize` *toward* the
architecture of Lean (and Agda, and Coq), not away from it.

## Where the designs diverge

In roughly descending order of importance.

### 1. `Prop` and proof irrelevance (the substantive semantic gap)

Martin-Löf / Thompson identify propositions with types completely:
`∃x.P` *is* `Σx.P`, so the first projection of an existence proof yields the
witness. `symbolize` takes this position — `FstProofSymbol.apply_proposition_type`
applied to `exists(x, P)` returns the witness's type.

Lean places `Exists` in an impredicative, proof-irrelevant universe `Prop` and
forbids *large elimination* out of it: a witness cannot be computed from an
`Exists` proof (only noncomputably via `Classical.choice`, or by using
`Σ` / `PSigma` / `Subtype` instead of `Exists`).

`symbolize`'s "strong ∃" is the Martin-Löf position; Lean deliberately rejects it.
It is a design choice, not a defect, but a `symbolize` derivation that uses `Fst`
on `∃` would not translate to Lean one-to-one unless `exists` were mapped to `Σ`.

### 2. The arity meta-language

`symbolize`'s `A0`, `ArityArrow`, `ArityCross` come from Nordström's *theory of
expressions* ([BN] ch. 3): a simply-typed meta-level syntax with arities,
abstraction and application, on top of which the object-level type theory is
defined.

Lean has no such layer. `Expr` is a single untyped-lambda-style term language
(de Bruijn indices, locally-nameless binders) and the object-level type checker
does all the work.

When the class hierarchy is replaced by a term datatype, a decision is needed:
keep arities as the "kind" discipline for terms (faithful to [BN]), or collapse
to a single term language and let the type checker enforce well-formedness
(what every implemented proof assistant does).

### 3. Fixed type formers vs. a general inductive schema

[BN] / [ST] present a fixed menu of type formers: `N`, Π, Σ, `+`, identity,
W-types, lists, a universe. `symbolize` mirrors this with one class per former
(`and_`, `or_`, `implies`, `forall`, `exists`, naturals with `succ` / `prim`),
each with its own `compute` method.

Lean has a general inductive-family schema and derives everything —
`Nat`, `And`, `Or`, `Eq`, `Exists` — from it, generating the recursor
automatically. That single mechanism (one recursor per inductive, plus
ι-reduction in the evaluator) is what removes the need for a separate Python
class and eager `compute` per operation, which is the structural problem the
README identifies.

### 4. Universes

`symbolize` has no universe hierarchy. This is fine at the propositional /
first-order level currently exercised, but quantifying over types requires one
(Nordström's `U` / `Set`; Lean's `Sort u`) to avoid Girard's paradox.

### 5. Equality and axioms

Both use an intensional identity type. Lean additionally has definitional η for
structures, proof irrelevance as a definitional equality, quotient types, and
axioms (`propext`, `Quot.sound`, `Classical.choice`). Pure Martin-Löf type theory
has none of these. `symbolize` does not yet implement an identity type.

### 6. Elaboration

`symbolize` is a raw derivation system: `Argument` trees are natural-deduction
style proof trees over explicit terms. Lean's *kernel* is comparable in spirit,
but nearly everything a user touches is the *elaborator* (unification, implicit
arguments, typeclasses, tactics). That layer is orthogonal to the kernel design
discussed here.

## Summary

| Aspect | `symbolize` ([BN]/[ST]) | Lean 4 |
|---|---|---|
| Core theory | Martin-Löf ITT | CIC variant |
| Propositions | = types (strong Σ for ∃) | `Prop`, proof-irrelevant, no large elim |
| Term syntax | arity-typed expressions | single `Expr` language, de Bruijn |
| Type formers | fixed set, one class each | general inductive schema + recursors |
| Evaluation | eager per-class `compute` | lazy `whnf`, cached defeq |
| Universes | none | `Sort u` hierarchy |
| Equality | (not yet implemented) | `Eq` inductive + η, quotients, axioms |
| Front end | explicit `Argument` trees | elaborator + tactics |

## Implications for the rewrite

- The term-based / lazy-evaluator design is the standard one; adopting it is
  low-risk and aligns with Lean, Agda and Coq.
- The one decision that makes `symbolize` *substantively* different from Lean is
  whether to keep Martin-Löf's strong ∃ / no-`Prop` stance. Decide this
  explicitly rather than inherit it by accident.
- If exporting derivations to Lean is ever a goal: use de Bruijn (or
  locally-nameless) binders in the term datatype, a `whnf`-style evaluator, and
  map `exists` to `Σ`.
- If fidelity to [BN]/[ST] is the goal: keep the strong Σ and document the
  difference.

*These notes are drawn from general knowledge of Lean 4's kernel design and
have not been verified against its source; check the details before relying on
them.*

## References

* [BN] Programming in Martin-Löf's Type Theory — Bengt Nordström, Kent
  Petersson, Jan M. Smith
* [ST] Type Theory & Functional Programming — Simon Thompson
* Lean 4 kernel: <https://github.com/leanprover/lean4/tree/master/src/kernel>
* Mario Carneiro, *The Type Theory of Lean* (MSc thesis, 2019) — a precise
  account of Lean's kernel theory
