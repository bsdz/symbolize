# Symbolize Agent Instructions

This document provides comprehensive guidelines for AI agents and developers working on the `symbolize` repository, a Mathematical Symbol Engine. Adherence to these instructions ensures consistency, quality, and maintainability across the codebase.

## 1. Project Goal and Direction

### What symbolize is for

The long-term aim is a symbolic mathematics system backed by type theory: an
eventual alternative to `sympy` in which every manipulation of an expression is
justified by a derivation that can be displayed and checked, rather than by an
opaque simplification routine. Nearer term, the type theory itself is the
deliverable (see `Term-based-design.md` and `Other-proof-engines.md`).

### Core commitments

These are settled decisions. Do not change them without the user's agreement.

- **Theory:** Martin-Lof intensional type theory as presented by Nordstrom et
  al. [BN] and Thompson [ST]. Propositions *are* types; `exists` is a strong
  sigma, so a witness is extractable. There is no `Prop` and no proof
  irrelevance. `Other-proof-engines.md` records how this relates to Lean 4.
- **Nothing evaluates on construction.** Building a term checks arity and
  nothing else; every reduction happens in the evaluator (`whnf`, `nf`,
  `defeq`) and only when asked. This is deliberate and is the answer to
  `sympy`'s `evaluate=False` problem: deferred is the default, so no flag has
  to be threaded through constructors and no tree needs rebuilding to suspend
  evaluation. Never add implicit evaluation to a constructor or a smart
  constructor.
- **Type formers are data, not classes.** A former is a `TypeFormer`
  declaration (formation, constructors, eliminators, computation rules) in a
  `Registry`. Adding an operation must not require a new Python class with its
  own `compute` method.
- **Terms are immutable** and compared structurally; binding is locally
  nameless, so alpha-equivalence is equality and substitution cannot capture.

### Where theorems come from

Both routes matter, and most theorems are expected to arrive by the second:

1. **Proved here.** The derivation layer (`symbolize/terms/derive.py`) builds
   judgements by the natural-deduction rules of [ST] ch. 4.
2. **Imported as statement-only stubs** from Lean 4 (possibly later Coq). Only
   the *statement* is translated, never the proof term; the stub is declared as
   a constant with a signature and no definition and no computation rules,
   which the registry already supports. Such a stub is an axiom: record its
   provenance (source system, version, declaration name, hash of the original
   statement) and keep derivations able to report the axioms they depend on.

When importing, the translation of the statement is the trusted step. Take
particular care with: Lean's `Exists` (proof-irrelevant, no large elimination)
which must NOT be mapped onto symbolize's strong `exists`, or a witness is
obtained that the source never proved; junk-valued definitions in the source
(`Nat.sub` truncation, division by zero); dropped instance or decidability
hypotheses; and `Prop`-valued statements gaining computational content. Prefer
verifying a translation by round-tripping the statement back to the source
system and checking it is definitionally equal to the original.

### Roadmap

Current order of work. Each step fits the existing design; steps 1-3 need no
changes to `term.py`, `eval.py` or `check.py`.

1. Identity type (`Id`, `refl`, `J`; `cong`, `symm`, `trans` as definitions) -
   needed before any equation can be stated, imported or rewritten with.
2. Axiom/stub declarations with provenance and axiom-usage tracking.
3. Rewriting driven by `Id` proofs.
4. Lean statement importer with a constant-mapping table and round-trip check.
5. Universes and algebraic structures, as the library grows.

## 2. Environment & Build

The project utilizes **Poetry** for robust dependency management and packaging.

### Setup
Ensure you have Poetry installed, then set up the environment:
```bash
# Install all dependencies (including dev)
poetry install
```

### Verification Commands

**Running Tests (`unittest`):**
Tests are the primary verification mechanism. Always run relevant tests after changes.
```bash
# Run the full test suite
poetry run python3 -m unittest discover tests

# Run a specific test file (e.g., test_groups.py)
poetry run python3 -m unittest tests/test_groups.py

# Run a specific test case (e.g., test_render in GroupTest)
poetry run python3 -m unittest tests.test_groups.GroupTest.test_render
```

**Linting & Formatting:**
Code must pass these checks before being considered complete.
```bash
# Format code with Black
poetry run black .

# Sort imports with Isort
poetry run isort .

# Format docstrings
poetry run docformatter --in-place --recursive .

# Type checking with Mypy
poetry run mypy .

# Linting with Flake8 (if installed; .flake8 config is present)
# Note: flake8 might need to be installed manually if not in poetry env
poetry run flake8 . || echo "flake8 not found/failed"
```

## 3. Code Style & Conventions

### Formatting & Layout
- **Style:** Strictly follow PEP 8.
- **Enforcement:** `black` is the authority on formatting. Run it on all modified files.
- **Line Length:** 80 characters (strictly enforced by `.flake8` and `black`).
- **Indentation:** Use 4 spaces. No tabs.
- **Imports:** 
    - Sorted automatically by `isort`.
    - Grouping: Standard Library -> Third Party -> Local/Project.
    - Avoid `from module import *` (wildcard imports) except in `__init__.py` where strictly necessary for exposure.

### Type Hinting
- **Requirement:** All new code must be fully typed.
- **Strictness:** Aim for `mypy` strict mode compatibility.
- **Generics:** Use `typing` module components (e.g., `List`, `Optional`, `Dict`, `Union`, `Any`) to ensure compatibility with Python 3.7+.
- **Return Types:** Always specify return types for functions and methods.

### Naming Conventions
- **Classes:** `PascalCase` (e.g., `GroupTest`, `SymbolEngine`, `Expression`).
- **Functions/Methods:** `snake_case` (e.g., `test_render`, `calculate_value`, `apply`).
- **Variables:** `snake_case` (e.g., `result`, `expression_list`).
- **Constants:** `UPPER_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_ARITY`).
- **Private Members:** Prefix with `_` (e.g., `_internal_helper`, `_arity`). Use `__` only for name mangling if strictly necessary.

### Documentation
- **Docstrings:** Mandatory for all public modules, classes, functions, and methods.
- **Style:** Follow standard Python docstring conventions (triple quotes).
- **Format:** Compatible with `docformatter`.
- **Content:** Briefly explain *what* the component does and *args/returns*.
- **License Headers:** All source files must include the standard copyright/license header:
  ```python
  """
  symbolize - Mathematical Symbol Engine
  Copyright (C) [Year]  [Name]
  Distributed under the terms of the GNU General Public License (GPL v3)
  """
  ```

### Error Handling
- **Specific Exceptions:** Catch specific exceptions (e.g., `ValueError`, `TypeError`) rather than bare `Exception`.
- **Custom Exceptions:** Use project-defined exceptions (e.g., `ExpressionException`, `PropositionException`) where applicable.
- **Message Clarity:** Exception messages should be descriptive and helpful for debugging.
- **Logging:** Use `warnings.warn` for deprecation or non-critical issues (as seen in `expression.py`).

## 4. Project Structure

- **`symbolize/terms/`**: The active core (see `Term-based-design.md`). New
  work goes here.
    - `arity.py`: Arities, the kinds of [BN] ch. 3.
    - `term.py`: The immutable `Term` datatype, arity-checked at construction.
    - `binding.py`: Locally-nameless abstraction, instantiation, substitution.
    - `decl.py`: `Signature`, `TypeFormer`, `Definition`, `Rule`, `Registry`.
    - `eval.py`: The lazy evaluator - `whnf`, `nf`, `defeq`.
    - `check.py`: `Context` and the bidirectional `Checker`.
    - `derive.py`: `Judgement`, the natural-deduction rules, `Argument`.
    - `library/`: Type formers (`pi`, `sigma`, `plus`, `falsum`, `nat`, `bool`)
      and the connectives as definitions over them (`logic.py`).
    - `render/`: Notation table plus typestring, unicode, LaTeX and graph
      renderers.
- **`symbolize/`** (legacy, kept working; being moved under a `legacy`
  submodule): `expressions/` (the class-per-operation `Expression` hierarchy),
  `logic/` (the older proofs and propositions), `definitions/`, `groups.py`,
  `natural.py`. Prefer `symbolize.terms` for anything new; touch the legacy
  tree only to keep it working or to port a feature across.
- **`tests/`**: Unit tests, mirroring the source structure.
- **`examples/`**: Usage examples, including paired notebooks that show the
  same derivations on the legacy and term-based cores.

## 5. Development Workflow for Agents

1.  **Analyze & Understand:**
    - Read relevant files using `read`.
    - Search for usage patterns using `grep` or `glob`.
    - Understand existing conventions before writing code.
    - Check for existing tests in `tests/` that cover the area of change.

2.  **Plan & Design:**
    - Formulate a clear plan for the change.
    - Identify impacted files.
    - Determine if new tests are needed.

3.  **Implement (Edit/Write):**
    - Make changes using `edit` or `write`.
    - Apply changes incrementally if complex.
    - **CRITICAL:** Ensure `Expression.apply` and related core methods maintain compatibility or are updated safely (e.g., handling arity checks).

4.  **Format & Lint:**
    - Run `poetry run black .`
    - Run `poetry run isort .`
    - Run `poetry run mypy .`

5.  **Verify & Test:**
    - Run relevant unit tests: `poetry run python3 -m unittest ...`
    - If a test fails, debug using `read` and print statements or a scratch script.
    - **Fixing Tests:** If a test is broken (like `test_prim_succ` was), analyze the traceback and core logic (e.g., `arity` mismatches) rather than blindly changing the test expectation.

## 6. Specific Rules & Caveats

- **Dependencies:** Do NOT add new dependencies (`poetry add`) unless explicitly instructed by the user. Rely on the standard library.
- **File Operations:** Always use **absolute paths** for file tools. Resolve relative paths against the project root.
- **Path Handling:** Use `os.path.join` or `pathlib.Path` for path construction.
- **Recursion & Arity:** Be careful with recursive structures in `Expression` (e.g., `prim` recursion). Arity checks can be strict; ensure logical consistency (e.g., higher-order function return types).
