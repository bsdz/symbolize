"""terms: term-based core (see Term-based-design.md).

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from .arity import A0, Arity, Arrow, Cross, Zero, arrow, cross
from .binding import (
    abstract,
    contains_free,
    free_vars,
    instantiate,
    open_abs,
    subst,
    subst_many,
    transform,
)
from .check import Checker, Context, TypingError
from .decl import (
    SET,
    DeclarationError,
    Definition,
    Param,
    Registry,
    Rule,
    Signature,
    TypeFormer,
    pvar,
)
from .eval import Evaluator, ReductionLimit, defeq, nf, whnf
from .term import (
    Abs,
    App,
    ArityError,
    Bound,
    Comb,
    Const,
    Sel,
    Term,
    TermError,
    Var,
    children,
    is_closed,
)

__all__ = [
    "A0",
    "SET",
    "DeclarationError",
    "Definition",
    "Checker",
    "Context",
    "Evaluator",
    "TypingError",
    "Param",
    "ReductionLimit",
    "Registry",
    "Rule",
    "Signature",
    "TypeFormer",
    "defeq",
    "nf",
    "pvar",
    "whnf",
    "Abs",
    "App",
    "Arity",
    "ArityError",
    "Arrow",
    "Bound",
    "Comb",
    "Const",
    "Cross",
    "Sel",
    "Term",
    "TermError",
    "Var",
    "Zero",
    "abstract",
    "arrow",
    "children",
    "contains_free",
    "cross",
    "free_vars",
    "instantiate",
    "is_closed",
    "open_abs",
    "subst",
    "subst_many",
    "transform",
]
