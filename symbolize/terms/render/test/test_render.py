"""Rendering: typestring, unicode, LaTeX and DOT, checked against the
outputs of README.md and examples/notebooks/Type Theory - Logic V2.ipynb.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import unittest

from symbolize.terms import A0, Arrow, Const, Var
from symbolize.terms.decl import SET
from symbolize.terms.derive import (Argument, Engine, cases, exists, family,
                                    forall,
                                    hyp, inl, inr, judge, pair, prim, set_var)
from symbolize.terms.library import (REAL, Falsum, Id, N, R, and_, apply,
                                     implies, lam, natrec, not_, numeral, or_,
                                     standard, succ, zero)
from symbolize.terms.library import add as nat_add
from symbolize.terms.render import (TextRenderer, dot, latex, tree, typestring,
                                    unicode)


class TestTerms(unittest.TestCase):
    def setUp(self):
        self.A, self.B, self.C = Var("A"), Var("B"), Var("C")
        self.x, self.y = Var("x"), Var("y")

    def test_readme_proposition(self):
        A, B, C = self.A, self.B, self.C
        t = implies(implies(A, B), implies(implies(B, C), implies(A, C)))
        self.assertEqual(
            latex(t),
            r"(A \Rightarrow B) \Rightarrow ((B \Rightarrow C) \Rightarrow (A \Rightarrow C))",
        )
        self.assertEqual(unicode(t), "(A ⟹ B) ⟹ ((B ⟹ C) ⟹ (A ⟹ C))")
        self.assertEqual(typestring(t), "⟹(⟹(A, B), ⟹(⟹(B, C), ⟹(A, C)))")
        # substituting ⊥ for C, as in the README
        u = t.subst(C, Falsum)
        self.assertEqual(
            latex(u),
            r"(A \Rightarrow B) \Rightarrow ((B \Rightarrow \bot) \Rightarrow (A \Rightarrow \bot))",
        )
        v = implies(implies(A, B), implies(not_(B), not_(A)))
        self.assertEqual(
            latex(v), r"(A \Rightarrow B) \Rightarrow (\neg(B) \Rightarrow \neg(A))"
        )
        self.assertEqual(unicode(v), "(A ⟹ B) ⟹ (¬(B) ⟹ ¬(A))")

    def test_connectives(self):
        A, B = self.A, self.B
        self.assertEqual(latex(and_(A, B)), r"A \land B")
        self.assertEqual(latex(or_(A, B)), r"A \lor B")
        self.assertEqual(latex(implies(or_(A, B), self.C)), r"(A \lor B) \Rightarrow C")
        self.assertEqual(unicode(and_(A, B)), "A ∧ B")
        self.assertEqual(typestring(or_(A, B)), "∨(A, B)")

    def test_quantifiers(self):
        P = Var("P", Arrow(A0, A0))
        x = self.x
        t = forall_(N, P(x).abstract(x))
        self.assertEqual(latex(t), r"\forall{x}.P(x)")
        self.assertEqual(unicode(t), "∀x.P(x)")
        self.assertEqual(typestring(t), "∀(N, (x)P(x))")
        # a family is shown eta-expanded
        self.assertEqual(latex(forall_(N, P)), r"\forall{x}.P(x)")
        # bound names avoid free variables and nested binders
        s = forall_(
            N, forall_(N, and_(P(x), P(Var("x'"))).abstract(Var("x'"))).abstract(x)
        )
        self.assertEqual(unicode(s), "∀x.∀x'.(P(x) ∧ P(x'))")
        # ∀x.P with a body that is compound
        u = forall_(N, implies(P(x), P(succ(x))).abstract(x))
        self.assertEqual(latex(u), r"\forall{x}.(P(x) \Rightarrow P(succ(x)))")
        e = exists_(N, P)
        self.assertEqual(latex(e), r"\exists{x}.P(x)")

    def test_lambda_and_apply(self):
        a, b, x = Var("a"), Var("b"), self.x
        e = Var("e")
        self.assertEqual(latex(lam(e.abstract(x))), r"\lambda{}(x).e")
        self.assertEqual(unicode(lam(e.abstract(x))), "λ(x).e")
        self.assertEqual(typestring(lam(e.abstract(x))), "λ((x)e)")
        self.assertEqual(latex(apply(a, x)), "a(x)")
        self.assertEqual(typestring(apply(a, x)), "apply(a, x)")
        body = apply(b, apply(a, x))
        proof = lam(lam(lam(body.abstract(x)).abstract(b)).abstract(a))
        self.assertEqual(
            latex(proof), r"\lambda{}(a).\lambda{}(b).\lambda{}(x).(b(a(x)))"
        )
        # applying a lambda directly
        self.assertEqual(latex(apply(lam(e.abstract(x)), a)), r"(\lambda{}(x).e)(a)")
        # a pair body is already parenthesised
        from symbolize.terms.library import pair

        self.assertEqual(latex(lam(pair(a, b).abstract(x))), r"\lambda{}(x).(a, b)")

    def test_pairs_and_projections(self):
        from symbolize.terms.library import fst, pair, snd

        p, q = Var("p"), Var("q")
        self.assertEqual(latex(pair(p, q)), "(p, q)")
        self.assertEqual(typestring(pair(p, q)), "pair(p, q)")
        self.assertEqual(latex(fst(pair(p, q))), "fst((p, q))")
        self.assertEqual(latex(snd(Var("r"))), "snd(r)")
        self.assertEqual(latex(inl_(p)), "inl(p)")

    def test_naturals(self):
        self.assertEqual(latex(N), r"\mathbb{N}")
        self.assertEqual(unicode(N), "ℕ")
        self.assertEqual(typestring(N), "N")
        self.assertEqual(latex(numeral(2)), "succ(succ(0))")
        K = Var("K", Arrow(A0, A0))
        n, y = Var("n"), self.y
        t = natrec(K, self.x, succ(zero), succ(y).abstract(n, y))
        self.assertEqual(unicode(t), "natrec(K, x, succ(0), (n, y)succ(y))")

    def test_aliases(self):
        p = Var("p")
        r = TextRenderer("latex", {p: "fst~p"})
        self.assertEqual(r.render(apply(p, self.x)), "fst~p(x)")

    def test_unregistered_constant_is_prefix(self):
        f = Const("f", Arrow(A0, A0))
        for style in (typestring, unicode, latex):
            self.assertEqual(style(f(self.x)), "f(x)")

    def test_graph(self):
        labels, edges = tree(implies(self.A, self.B))
        self.assertEqual(labels, ["⟹", "A", "B"])
        self.assertEqual(edges, [(0, 1), (0, 2)])
        src = dot(lam(apply(Var("f"), self.x).abstract(self.x)))
        self.assertIn("digraph", src)
        self.assertIn('label="λ"', src)
        self.assertIn('label="(x)"', src)
        self.assertIn("->", src)
        self.assertEqual(
            implies(self.A, self.B).repr_dot(), dot(implies(self.A, self.B))
        )


def forall_(dom, fam):
    from symbolize.terms.library import forall

    return forall(dom, fam)


def exists_(dom, fam):
    from symbolize.terms.library import exists

    return exists(dom, fam)


def inl_(a):
    from symbolize.terms.library import inl

    return inl(a)


class TestJudgements(unittest.TestCase):
    """Cells of Type Theory - Logic V2.ipynb."""

    def setUp(self):
        # A private engine. The module-level DEFAULT caches weak head normal
        # forms for the life of the process, and because display hints are
        # excluded from term equality, a cache hit can come back carrying
        # another test's binder names.
        self.engine = Engine(standard())
        self.A, self.B, self.C = (
            set_var(name, engine=self.engine) for name in ("A", "B", "C")
        )

    def test_conjunction(self):
        A, B = self.A, self.B
        p, q = hyp("p", A), hyp("q", B)
        r = pair(p, q)
        self.assertEqual(r.repr_latex(), r"(p, q) : A \land B")
        self.assertEqual(r.fst.repr_latex(), r"fst((p, q)) : A")
        r2 = hyp("r", A & B)
        self.assertEqual(r2.fst.repr_latex(), "fst(r) : A")
        self.assertEqual(r2.snd.repr_unicode(), "snd(r) : B")
        self.assertEqual(r2.snd.repr_typestring(), "snd(r) : B")
        self.assertEqual(
            Argument([r2], r2.fst).repr_latex(), r"\frac{r : A \land B}{fst(r) : A}"
        )

    def test_implication(self):
        A, B = self.A, self.B
        x, e = hyp("x", A), hyp("e", B)
        self.assertEqual(
            e.abstract(x).repr_latex(), r"\lambda{}(x).e : A \Rightarrow B"
        )
        arg = Argument([e], e.abstract(x), discharges=[x], label=r"\Rightarrow{I}")
        self.assertEqual(
            arg.repr_latex(),
            r"\frac{\begin{matrix}[x : A]\\ \vdots\\ e : B\\ \end{matrix}}"
            r"{\lambda{}(x).e : A \Rightarrow B}(\Rightarrow{I})",
        )
        q, a = hyp("q", A >> B), hyp("a", A)
        self.assertEqual(q(a).repr_latex(), "q(a) : B")
        self.assertEqual(q(a)._repr_latex_(), "$$q(a) : B$$")

    def test_disjunction(self):
        A, B = self.A, self.B
        q, r = hyp("q", A), hyp("r", B)
        self.assertEqual(inl(q, B).repr_latex(), r"inl(q) : A \lor B")
        self.assertEqual(inr(r, A).repr_latex(), r"inr(r) : A \lor B")

    def test_readme_derivation(self):
        """[ST] p83-84, as in README.md"""
        A, B, C = self.A, self.B, self.C
        a, b, x = hyp("a", A >> B), hyp("b", B >> C), hyp("x", A)
        arg1 = Argument([x, a], a(x))
        self.assertEqual(
            arg1.repr_latex(), r"\frac{x : A \quad a : A \Rightarrow B}{a(x) : B}"
        )
        arg2 = Argument([arg1, b], b(arg1.conclusion))
        arg3 = Argument([arg2, x], arg2.conclusion.abstract(x))
        arg4 = Argument([arg2, x], arg3.conclusion.abstract(b))
        arg5 = Argument([arg2, x], arg4.conclusion.abstract(a))
        self.assertEqual(
            arg5.repr_latex(),
            r"\frac{\frac{\frac{x : A \quad a : A \Rightarrow B}{a(x) : B} \quad b : B \Rightarrow C}"
            r"{b(a(x)) : C} \quad x : A}"
            r"{\lambda{}(a).\lambda{}(b).\lambda{}(x).(b(a(x))) : "
            r"(A \Rightarrow B) \Rightarrow ((B \Rightarrow C) \Rightarrow (A \Rightarrow C))}",
        )
        self.assertEqual(
            arg5.conclusion.type.subst(C.term, Falsum).repr_latex(),
            r"(A \Rightarrow B) \Rightarrow ((B \Rightarrow \bot) \Rightarrow (A \Rightarrow \bot))",
        )

    def test_cases_with_aliases(self):
        A, B, C = self.A, self.B, self.C
        z = hyp("z", A | B)
        p = hyp("p", (A >> C) & (B >> C))
        f, g = p.fst.alias("fst~p"), p.snd.alias("snd~p")
        r = cases(z, f, g)
        self.assertEqual(r.repr_latex(), "cases(z, fst~p, snd~p) : C")
        self.assertEqual(f.repr_latex(), r"fst~p : A \Rightarrow C")
        self.assertEqual(
            r.abstract(z).abstract(p).repr_latex(),
            r"\lambda{}(p).\lambda{}(z).(cases(z, fst~p, snd~p)) : "
            r"((A \Rightarrow C) \land (B \Rightarrow C)) \Rightarrow ((A \lor B) \Rightarrow C)",
        )
        arg = Argument([z, f, g], r)
        self.assertEqual(
            arg.repr_latex(),
            r"\frac{z : A \lor B \quad fst~p : A \Rightarrow C \quad snd~p : B \Rightarrow C}"
            r"{cases(z, fst~p, snd~p) : C}",
        )

    def test_quantifiers(self):
        A = self.A
        x, a = hyp("x", A), hyp("a", A)
        P = family("P", A, engine=self.engine)
        f = hyp("f", forall(x, P(x)))
        self.assertEqual(f.repr_latex(), r"f : \forall{x}.P(x)")
        self.assertEqual(f(a).repr_latex(), "f(a) : P(a)")
        self.assertEqual(
            f(x).abstract(x).repr_latex(), r"\lambda{}(x).(f(x)) : \forall{x}.P(x)"
        )
        p = hyp("p", P(a))
        self.assertEqual(pair(a, p).repr_latex(), r"(a, p) : \exists{a}.P(a)")
        q = hyp("q", exists(x, P(x)))
        self.assertEqual(q.fst.repr_latex(), "fst(q) : A")
        self.assertEqual(q.snd.repr_latex(), "snd(q) : P(fst(q))")
        self.assertEqual(P.repr_latex(), "P(z)")
        self.assertEqual(P(a).repr_latex(), "P(a)")
        self.assertEqual(A.repr_latex(), "A")
        self.assertEqual(
            Argument([a, f], f(a), label=r"\forall{E}").repr_latex(),
            r"\frac{a : A \quad f : \forall{x}.P(x)}{f(a) : P(a)}(\forall{E})",
        )

    def test_context(self):
        A = self.A
        x = hyp("x", A)
        P = family("P", A, engine=self.engine)
        p = hyp("p", P(x))
        self.assertEqual(p.repr_context(), "[A : Set, P(z), x : A, p : P(x)]")

    def test_naturals(self):
        Nset = judge(N, SET, engine=self.engine)
        x, y, n = hyp("x", Nset), hyp("y", Nset), hyp("n", Nset)
        f = (
            judge(succ(y.term), N, y.ctx, engine=self.engine)
            .abstract(y)
            .abstract(n)
        )
        addone = prim(x, judge(succ(zero), N, engine=self.engine), f).abstract(x)
        self.assertEqual(
            addone.repr_unicode(),
            "λ(x).(natrec((_)ℕ, x, succ(0), (x', y)succ(y))) : ℕ ⟹ ℕ",
        )

    def test_unicode_argument(self):
        A, B = self.A, self.B
        x, a = hyp("x", A), hyp("a", A >> B)
        text = Argument([x, a], a(x), label="⇒E").repr_unicode()
        self.assertEqual(text.splitlines()[0], "x : A   a : A ⟹ B")
        self.assertEqual(text.splitlines()[-1], "a(x) : B")


class TestArithmetic(unittest.TestCase):
    """Operators with a precedence: parentheses only where they are needed.

    Built from the ring's constants directly, so rendering is tested without
    an engine.
    """

    def setUp(self):
        self.x, self.y, self.z = Var("x"), Var("y"), Var("z")
        self.add, self.mul = REAL.add, REAL.mul
        self.sub, self.neg, self.pow = REAL.sub, REAL.neg, REAL.pow

    def check(self, term, text, tex):
        self.assertEqual(unicode(term), text)
        self.assertEqual(latex(term), tex)

    def test_precedence(self):
        x, y, z = self.x, self.y, self.z
        self.check(self.add(x, self.mul(y, z)), "x + y ⋅ z", r"x + y \cdot z")
        self.check(
            self.mul(self.add(x, y), z), "(x + y) ⋅ z", r"(x + y) \cdot z"
        )

    def test_names_are_escaped_for_latex(self):
        """An underscore in a law's name would otherwise subscript the next
        letter: ``R.mul_{a}dd``."""
        law = REAL.mul_add(self.x, self.y, Var("z_1"))
        self.check(law, "R.mul_add(x, y, z_1)", r"R.mul\_add(x, y, z\_1)")

    def test_infix_operators_associate_to_the_left(self):
        """Grouping is shown exactly where it differs from the reading
        convention, since a proof has to know which one it has."""
        x, y, z = self.x, self.y, self.z
        self.check(self.add(self.add(x, y), z), "x + y + z", "x + y + z")
        self.check(self.add(x, self.add(y, z)), "x + (y + z)", "x + (y + z)")
        self.check(self.sub(self.sub(x, y), z), "x - y - z", "x - y - z")
        self.check(self.sub(x, self.sub(y, z)), "x - (y - z)", "x - (y - z)")

    def test_unary_minus(self):
        x, y = self.x, self.y
        self.check(self.neg(x), "-x", "-x")
        self.check(self.neg(self.add(x, y)), "-(x + y)", "-(x + y)")
        self.check(self.mul(self.neg(x), y), "-x ⋅ y", r"-x \cdot y")
        self.check(self.neg(self.neg(x)), "-(-x)", "-(-x)")

    def test_powers(self):
        x, y = self.x, self.y
        two, three = numeral(2), numeral(3)
        self.check(self.pow(x, two), "x²", "x^{2}")
        self.check(self.pow(self.add(x, y), two), "(x + y)²", "(x + y)^{2}")
        self.check(self.neg(self.pow(x, two)), "-x²", "-x^{2}")
        self.check(self.pow(self.neg(x), two), "(-x)²", "(-x)^{2}")
        self.check(self.pow(self.pow(x, two), three), "(x²)³", "(x^{2})^{3}")
        self.check(
            self.mul(y, self.pow(x, numeral(12))), "y ⋅ x¹²", r"y \cdot x^{12}"
        )

    def test_a_variable_exponent(self):
        n = Var("n")
        self.check(self.pow(self.x, n), "x^n", "x^{n}")
        self.check(self.pow(self.x, succ(n)), "x^succ(n)", "x^{succ(n)}")

    def test_literals(self):
        self.check(REAL.zero, "0", "0")
        self.check(REAL.cast(numeral(7)), "7", "7")
        self.check(self.pow(REAL.cast(numeral(2)), numeral(3)), "2³", "2^{3}")

    def test_a_cast_that_is_not_a_literal(self):
        n = Var("n")
        self.check(REAL.cast(n), "↑n", r"{\uparrow}n")
        self.check(
            self.pow(REAL.cast(n), numeral(2)), "(↑n)²", r"({\uparrow}n)^{2}"
        )

    def test_equations_need_no_brackets_around_arithmetic(self):
        x, y = self.x, self.y
        t = Id(R, self.add(x, y), self.add(y, x))
        self.check(t, "x + y = y + x", "x + y = y + x")

    def test_operators_without_precedence_keep_their_brackets(self):
        """N's addition has no precedence, so its rendering is unchanged."""
        n = Var("n")
        self.assertEqual(unicode(Id(N, nat_add(zero, n), n)), "(0 + n) = n")
        self.assertEqual(
            unicode(and_(Id(R, self.x, self.y), Id(R, self.y, self.x))),
            "(x = y) ∧ (y = x)",
        )

    def test_typestring_is_faithful(self):
        t = self.pow(self.add(self.x, REAL.one), numeral(2))
        self.assertEqual(typestring(t), "R.pow(R.add(x, R.one), succ(succ(0)))")


if __name__ == "__main__":
    unittest.main()
