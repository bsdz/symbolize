# Symbolize Agent Instructions

This document provides comprehensive guidelines for AI agents and developers working on the `symbolize` repository, a Mathematical Symbol Engine. Adherence to these instructions ensures consistency, quality, and maintainability across the codebase.

## 1. Environment & Build

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

## 2. Code Style & Conventions

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

## 3. Project Structure

- **`symbolize/`**: Core package source code.
    - **`expressions/`**: Base expression logic, arity, and rendering.
        - `expression.py`: Core `Expression` class.
        - `arity.py`: Arity definitions.
    - **`logic/`**: Logic and type theory implementations.
        - `typetheory/`: Proofs, propositions, natural numbers.
            - `proof.py`: Proof expression logic.
            - `proposition.py`: Proposition definitions.
            - `natural.py`: Natural number definitions.
    - **`definitions/`**: Mathematical definitions.
    - **`groups.py`**: Group theory implementations.
- **`tests/`**: Unit tests, mirroring the source structure.
- **`examples/`**: Usage examples.

## 4. Development Workflow for Agents

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

## 5. Specific Rules & Caveats

- **Dependencies:** Do NOT add new dependencies (`poetry add`) unless explicitly instructed by the user. Rely on the standard library.
- **File Operations:** Always use **absolute paths** for file tools. Resolve relative paths against the project root.
- **Path Handling:** Use `os.path.join` or `pathlib.Path` for path construction.
- **Recursion & Arity:** Be careful with recursive structures in `Expression` (e.g., `prim` recursion). Arity checks can be strict; ensure logical consistency (e.g., higher-order function return types).
