"""Importing Lean 4 statements, and exporting them back for checking.

Most fixtures here are hand-written ``Expr`` JSON of the shape
``interop/Export.lean`` produces, so no Lean toolchain is needed to test the
translation. ``TestRealExport`` additionally runs against
``fixtures/lean_nat.json``, a dump captured from a real ``#symbolize_export``
on Lean 4.34.1, which is what guards against the hand-written shapes drifting
from what Lean actually emits.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

import json
import os
import unittest

from symbolize.terms import A0, Abs, Var
from symbolize.terms.decl import SET
from symbolize.terms.derive import Engine, family, hyp, judge, rewrite
from symbolize.terms.interop import (LeanExportError, LeanImporter,
                                     LeanImportError, Rule, round_trip,
                                     round_trip_file, to_lean)
from symbolize.terms.library import N, add, implies, numeral, standard, zero


def const(name, *args):
    """A curried Lean application of a constant."""
    expr = {"kind": "const", "name": name, "levels": []}
    for arg in args:
        expr = {"kind": "app", "fn": expr, "arg": arg}
    return expr


def forall(name, domain, body):
    return {
        "kind": "forallE",
        "binderName": name,
        "binderType": domain,
        "body": body,
    }


def lam(name, domain, body):
    return {"kind": "lam", "binderName": name, "binderType": domain, "body": body}


def bvar(index):
    return {"kind": "bvar", "index": index}


def lit(value):
    return {"kind": "lit", "natVal": value}


NAT = const("Nat")
PROP = {"kind": "sort", "level": "0"}


def eq(domain, left, right):
    return const("Eq", domain, left, right)


class LeanTest(unittest.TestCase):
    def setUp(self):
        self.engine = Engine(standard())
        self.importer = LeanImporter(self.engine, version="4.23.0")
        self.N = judge(N, SET, engine=self.engine)

    def term(self, expr):
        return self.importer.term(expr)


class TestTranslation(LeanTest):
    def test_constants_and_literals(self):
        self.assertEqual(self.term(NAT), N)
        self.assertEqual(self.term(const("Nat.zero")), zero)
        self.assertEqual(self.term(lit(3)), numeral(3))
        self.assertEqual(self.term(const("Nat.succ", lit(1))), numeral(2))

    def test_arithmetic(self):
        m, n = lit(1), lit(2)
        self.assertEqual(self.term(const("Nat.add", m, n)), add(numeral(1), numeral(2)))
        # the bundled operator, with its type and instance arguments dropped
        bundled = const("HAdd.hAdd", NAT, NAT, NAT, const("instAddNat"), m, n)
        self.importer.rules["instAddNat"] = Rule(0, head=zero)  # never inspected
        self.assertEqual(self.term(bundled), add(numeral(1), numeral(2)))

    def test_ofnat_wrapper_is_unwrapped(self):
        wrapped = const("OfNat.ofNat", NAT, lit(2), const("Nat.zero"))
        self.assertEqual(self.term(wrapped), numeral(2))

    def test_equality(self):
        from symbolize.terms.library import Id

        self.assertEqual(
            self.term(eq(NAT, lit(0), lit(0))), Id(N, numeral(0), numeral(0))
        )

    def test_dependent_binder_is_forall(self):
        """theorem (n : Nat) : n = n"""
        statement = forall("n", NAT, eq(NAT, bvar(0), bvar(0)))
        j = self.importer.statement(statement)
        self.assertTrue(j.is_set)
        self.assertEqual(j.repr_unicode(), "∀n.n = n")

    def test_unused_binder_is_an_implication(self):
        """theorem : Nat -> Nat = Nat  (the binder is not used)"""
        statement = forall("h", eq(NAT, lit(0), lit(0)), eq(NAT, lit(1), lit(1)))
        j = self.importer.statement(statement)
        self.assertEqual(j.repr_unicode(), "(0 = 0) ⟹ (succ(0) = succ(0))")
        self.assertEqual(
            j.term,
            implies(
                self.term(eq(NAT, lit(0), lit(0))),
                self.term(eq(NAT, lit(1), lit(1))),
            ),
        )

    def test_nested_binders_keep_their_indices(self):
        """theorem (m n : Nat) : m + n = n + m"""
        inner = eq(
            NAT,
            const("Nat.add", bvar(1), bvar(0)),
            const("Nat.add", bvar(0), bvar(1)),
        )
        statement = forall("m", NAT, forall("n", NAT, inner))
        j = self.importer.statement(statement)
        self.assertEqual(j.repr_unicode(), "∀m.∀n.(m + n) = (n + m)")

    def test_lambda(self):
        body = lam("x", NAT, const("Nat.succ", bvar(0)))
        term = self.term(body)
        self.assertEqual(term.repr_unicode(), "λ(x).(succ(x))")

    def test_let_is_expanded(self):
        expr = {
            "kind": "letE",
            "name": "k",
            "type": NAT,
            "value": lit(2),
            "body": eq(NAT, bvar(0), bvar(0)),
        }
        from symbolize.terms.library import Id

        self.assertEqual(self.term(expr), Id(N, numeral(2), numeral(2)))

    def test_mdata_is_transparent(self):
        wrapped = {"kind": "mdata", "expr": NAT}
        self.assertEqual(self.term(wrapped), N)
        self.assertEqual(
            self.term({"kind": "mdata", "expr": const("Nat.succ", lit(0))}),
            numeral(1),
        )

    def test_application_of_a_bound_function(self):
        """theorem (f : Nat -> Nat) : f 0 = f 0"""
        fn_type = forall("_", NAT, NAT)
        applied = {"kind": "app", "fn": bvar(0), "arg": lit(0)}
        statement = forall("f", fn_type, eq(NAT, applied, applied))
        j = self.importer.statement(statement)
        self.assertEqual(j.repr_unicode(), "∀f.f(0) = f(0)")

    def test_statement_must_type_check(self):
        """A well formed translation that is not a set is still refused."""
        from symbolize.terms.check import TypingError

        bad = eq(NAT, lit(0), const("Bool.true"))
        with self.assertRaises(TypingError):
            self.importer.statement(bad)


class TestRefusals(LeanTest):
    def assertRefused(self, expr, fragment):
        with self.assertRaises(LeanImportError) as raised:
            self.term(expr)
        self.assertIn(fragment, str(raised.exception))

    def test_exists_is_refused(self):
        body = lam("x", NAT, eq(NAT, bvar(0), bvar(0)))
        self.assertRefused(const("Exists", NAT, body), "strong sigma")

    def test_sorts_are_refused(self):
        self.assertRefused(forall("p", PROP, bvar(0)), "no universes")
        self.assertRefused(PROP, "no universes")

    def test_unknown_constant_names_itself(self):
        self.assertRefused(const("Nat.gcd", lit(1), lit(2)), "'Nat.gcd'")

    def test_arity_mismatch(self):
        self.assertRefused(const("Nat.add", lit(1)), "takes 2 argument(s)")
        self.assertRefused(const("Eq", NAT, lit(1), lit(1), lit(1)), "applies it to 4")

    def test_open_or_incomplete_terms(self):
        self.assertRefused({"kind": "fvar", "name": "x"}, "not closed")
        self.assertRefused({"kind": "mvar", "name": "m"}, "metavariable")

    def test_projection(self):
        self.assertRefused(
            {"kind": "proj", "structName": "And", "idx": 0, "expr": NAT},
            "no structures",
        )

    def test_junk_valued_operations(self):
        self.assertRefused(const("Nat.sub", lit(1), lit(2)), "truncates at zero")
        self.assertRefused(
            const("HDiv.hDiv", NAT, NAT, NAT, NAT, lit(1), lit(0)), "junk-valued"
        )

    def test_classical_and_unit(self):
        self.assertRefused(const("Classical.em", NAT), "intuitionistic")
        self.assertRefused(const("True"), "no unit set")

    def test_iff_explains_the_round_trip_problem(self):
        self.assertRefused(const("Iff", NAT, NAT), "round-trip")

    def test_unsupported_kind(self):
        self.assertRefused({"kind": "banana"}, "Unsupported Expr kind")
        with self.assertRaises(LeanImportError):
            self.term("not an object")

    def test_string_literals(self):
        self.assertRefused({"kind": "lit", "strVal": "hi"}, "natural number")

    def test_a_custom_rule_can_lift_a_refusal(self):
        """The table is the policy: a caller who accepts a caveat overrides it."""
        importer = LeanImporter(
            self.engine, rules={"Nat.gcd": Rule(2, head=add, keep=(0, 1))}
        )
        self.assertEqual(
            importer.term(const("Nat.gcd", lit(1), lit(1))),
            add(numeral(1), numeral(1)),
        )


class TestDeclaration(LeanTest):
    def test_theorem_becomes_an_axiom(self):
        statement = forall(
            "n", NAT, eq(NAT, const("Nat.add", bvar(0), lit(0)), bvar(0))
        )
        j = self.importer.theorem(
            statement,
            "add_zero",
            lean_name="Nat.add_zero",
            statement="theorem Nat.add_zero (n : Nat) : n + 0 = n",
        )
        self.assertEqual(j.repr_unicode(), "add_zero : ∀n.(n + 0) = n")
        self.assertEqual([c.name for c in j.axioms], ["add_zero"])
        record = self.engine.registry.provenance(j.axioms[0])
        self.assertEqual(record.system, "lean4")
        self.assertEqual(record.version, "4.23.0")
        self.assertEqual(record.name, "Nat.add_zero")
        self.assertEqual(len(record.digest), 16)
        self.assertIn("lean4 4.23.0: Nat.add_zero", j.trust_report())

    def test_load_several(self):
        export = {
            "version": "4.23.0",
            "declarations": [
                {
                    "name": "Nat.add_zero",
                    "statement": "theorem Nat.add_zero (n : Nat) : n + 0 = n",
                    "type": forall(
                        "n", NAT, eq(NAT, const("Nat.add", bvar(0), lit(0)), bvar(0))
                    ),
                },
                {
                    "name": "Nat.zero_add",
                    "symbolizeName": "zero_add",
                    "statement": "theorem Nat.zero_add (n : Nat) : 0 + n = n",
                    "type": forall(
                        "n", NAT, eq(NAT, const("Nat.add", lit(0), bvar(0)), bvar(0))
                    ),
                },
            ],
        }
        imported = LeanImporter(self.engine).load(json.dumps(export))
        self.assertEqual(sorted(imported), ["Nat_add_zero", "zero_add"])
        self.assertEqual(
            imported["zero_add"].repr_unicode(), "zero_add : ∀n.(0 + n) = n"
        )
        self.assertEqual(
            [c.name for c in self.engine.registry.axioms()],
            ["Nat_add_zero", "zero_add"],
        )


class TestUse(LeanTest):
    """The point of importing: rewriting with a law proved elsewhere."""

    def test_rewrite_with_an_imported_law(self):
        zero_add = self.importer.theorem(
            forall("n", NAT, eq(NAT, const("Nat.add", lit(0), bvar(0)), bvar(0))),
            "zero_add",
            lean_name="Nat.zero_add",
            statement="theorem Nat.zero_add (n : Nat) : 0 + n = n",
        )
        m = hyp("m", self.N)
        # 0 + m is stuck: add recurses on its second argument, so this is not
        # a definitional equality and the imported law is doing real work
        sum_ = judge(add(zero, m.term), N, m.ctx, engine=self.engine)
        self.assertFalse(sum_.defeq(m))

        Q = family("Q", self.N, engine=self.engine)
        q = hyp("q", Q(sum_))
        rewritten = rewrite(q, zero_add(m))
        self.assertTrue(rewritten.has_type(Q(m)))
        self.engine.checker.check(rewritten.ctx, rewritten.term, rewritten.type)
        self.assertEqual([c.name for c in rewritten.axioms], ["zero_add"])
        self.assertIn("Nat.zero_add", rewritten.trust_report())

    def test_definitional_facts_need_no_import(self):
        """m + 0 = m holds by computation, so refl proves it."""
        m = hyp("m", self.N)
        sum_ = judge(add(m.term, zero), N, m.ctx, engine=self.engine)
        self.assertTrue(sum_.defeq(m))
        self.assertTrue(sum_.refl.has_type(sum_.eq(m)))
        self.assertEqual(sum_.refl.axioms, ())


class TestExport(LeanTest):
    def test_statement_round_trip_text(self):
        statement = forall(
            "n", NAT, eq(NAT, const("Nat.add", bvar(0), lit(0)), bvar(0))
        )
        j = self.importer.theorem(statement, "add_zero", lean_name="Nat.add_zero")
        self.assertEqual(
            to_lean(j.type),
            "(∀ (n : Nat), (@Eq Nat (Nat.add n Nat.zero) n))",
        )
        check = round_trip(j, "Nat.add_zero")
        text = str(check)
        self.assertIn("example :", text)
        self.assertIn(":= Nat.add_zero", text)
        self.assertIn("imported as add_zero", text)

    def test_file(self):
        statement = forall("n", NAT, eq(NAT, bvar(0), bvar(0)))
        j = self.importer.theorem(statement, "self_eq", lean_name="Eq.refl")
        text = round_trip_file([round_trip(j, "Eq.refl")], imports=("Init", "Std"))
        self.assertIn("import Init", text)
        self.assertIn("import Std", text)
        self.assertIn("Generated by symbolize", text)
        self.assertIn(":= Eq.refl", text)

    def test_connectives_and_implication(self):
        from symbolize.terms.library import and_, not_, or_

        A = judge(N, SET, engine=self.engine)
        self.assertEqual(to_lean(and_(N, N)), "(And Nat Nat)")
        self.assertEqual(to_lean(or_(N, N)), "(Or Nat Nat)")
        self.assertEqual(to_lean(not_(N)), "(Not Nat)")
        self.assertEqual(to_lean(implies(N, N)), "(Nat → Nat)")
        self.assertIsNotNone(A)

    def test_lambda_and_apply(self):
        from symbolize.terms.library import apply
        from symbolize.terms.library import lam as lam_const

        x = Var("x")
        self.assertEqual(to_lean(lam_const(x.abstract(x))), "(fun x => x)")
        self.assertEqual(to_lean(apply(zero, zero)), "(Nat.zero Nat.zero)")

    def test_unexportable_terms_are_refused(self):
        from symbolize.terms.library import Sigma, exists

        x = Var("x")
        with self.assertRaises(LeanExportError) as raised:
            to_lean(exists(N, x.abstract(x)))
        self.assertIn("strong existential", str(raised.exception))
        with self.assertRaises(LeanExportError):
            to_lean(Sigma(N, x.abstract(x)))  # no Lean name
        with self.assertRaises(LeanExportError):
            to_lean(Abs((A0,), zero))  # a bare abstraction
        with self.assertRaises(LeanExportError):
            to_lean(Var("A"))  # not closed

    def test_binder_names_are_freshened(self):
        from symbolize.terms.library import forall as forall_const

        x = Var("x")
        inner = forall_const(N, x.abstract(x))
        outer = forall_const(N, inner.abstract(x))
        self.assertEqual(
            to_lean(outer),
            "(∀ (x : Nat), (∀ (x' : Nat), x'))",
        )


FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "lean_nat.json")


class TestRealExport(LeanTest):
    """Against a dump captured from a real Lean 4.34.1 ``#symbolize_export``.

    The hand-written fixtures above encode what this module *believes* Lean
    emits; this one encodes what it actually emitted, so the two drifting
    apart shows up as a failure here.
    """

    def setUp(self):
        super().setUp()
        with open(FIXTURE, encoding="utf-8") as handle:
            self.export = json.load(handle)
        self.decls = {e["name"]: e for e in self.export["declarations"]}

    def translate(self, name):
        return self.term(self.decls[name]["type"])

    def test_the_dump_is_a_real_one(self):
        self.assertEqual(self.export["version"], "4.34.1")
        self.assertIn("Nat.add_zero", self.decls)

    def test_bundled_operators_are_unwrapped(self):
        """``n + 0`` reaches us as ``HAdd.hAdd`` over ``instHAdd``/
        ``instAddNat`` with ``OfNat.ofNat``/``instOfNatNat`` for the numeral;
        the instance arguments are dropped by ``keep``, so they never need
        rules of their own."""
        raw = json.dumps(self.decls["Nat.add_zero"]["type"])
        for wrapper in (
            "HAdd.hAdd",
            "instHAdd",
            "instAddNat",
            "OfNat.ofNat",
            "instOfNatNat",
        ):
            self.assertIn(wrapper, raw)
        from symbolize.terms.library import Id
        from symbolize.terms.library import forall as forall_const

        x = Var("n")
        self.assertEqual(
            self.translate("Nat.add_zero"),
            forall_const(N, Id(N, add(x, zero), x).abstract(x)),
        )

    def test_statements_translate(self):
        expected = {
            "Nat.add_zero": "∀(N, (n)Id(N, add(n, 0), n))",
            "Nat.zero_add": "∀(N, (n)Id(N, add(0, n), n))",
            "Nat.add_comm": "∀(N, (n)∀(N, (m)Id(N, add(n, m), add(m, n))))",
            "Nat.mul_comm": "∀(N, (n)∀(N, (m)Id(N, mul(n, m), mul(m, n))))",
            "Nat.mul_one": "∀(N, (n)Id(N, mul(n, succ(0)), n))",
            "Nat.add_assoc": (
                "∀(N, (n)∀(N, (m)∀(N, (k)"
                "Id(N, add(add(n, m), k), add(n, add(m, k))))))"
            ),
        }
        for name, text in expected.items():
            with self.subTest(name):
                got = self.importer.statement(self.decls[name]["type"])
                self.assertEqual(got.term.repr_typestring(), text)

    def test_real_refusals(self):
        """What the source really contains that must not be imported."""
        cases = {
            "Nat.sub_self": "HSub.hSub",  # truncating subtraction
            "Nat.le_refl": "LE.le",  # no order in the library
            "Eq.refl": "universe",  # Sort u_1
            "symbolize_fixture_exists": "strong sigma",  # proof-irrelevant ∃
        }
        for name, expected in cases.items():
            with self.subTest(name):
                with self.assertRaises(LeanImportError) as raised:
                    self.importer.statement(self.decls[name]["type"])
                self.assertIn(expected, str(raised.exception))

    def test_load_declares_the_importable_ones(self):
        """``load`` over the whole dump, keeping only what translates."""
        importable = [
            e
            for e in self.export["declarations"]
            if e["name"].startswith("Nat.")
            and e["name"] not in ("Nat.sub_self", "Nat.le_refl")
        ]
        source = json.dumps(
            {"version": self.export["version"], "declarations": importable}
        )
        got = LeanImporter(self.engine).load(source)
        self.assertEqual(
            sorted(got),
            [
                "Nat_add_assoc",
                "Nat_add_comm",
                "Nat_add_zero",
                "Nat_mul_comm",
                "Nat_mul_one",
                "Nat_zero_add",
            ],
        )
        for local, judgement in got.items():
            with self.subTest(local):
                self.assertEqual([c.name for c in judgement.axioms], [local])
                record = self.engine.registry.provenance(judgement.axioms[0])
                self.assertEqual(record.system, "lean4")
                self.assertEqual(record.version, "4.34.1")
                self.assertTrue(record.digest)

    def test_round_trip_text_matches_what_lean_accepted(self):
        """These exact ``example`` lines were compiled by Lean 4.34.1."""
        got = LeanImporter(self.engine).load(
            json.dumps(
                {
                    "version": "4.34.1",
                    "declarations": [self.decls["Nat.add_zero"]],
                }
            )
        )
        check = round_trip(got["Nat_add_zero"], "Nat.add_zero")
        self.assertEqual(
            check.statement, "(∀ (n : Nat), (@Eq Nat (Nat.add n Nat.zero) n))"
        )
        self.assertIn(
            "example : (∀ (n : Nat), (@Eq Nat (Nat.add n Nat.zero) n)) "
            ":= Nat.add_zero",
            round_trip_file([check]),
        )


if __name__ == "__main__":
    unittest.main()
