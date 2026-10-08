/-
Export Lean 4 statements for symbolize.

  #symbolize_export Nat.add_zero Nat.zero_add

prints a JSON object holding each declaration's *type* as a faithful dump of
its kernel `Expr`, which `symbolize.terms.interop.lean.LeanImporter.load`
consumes. Proof terms are never exported: only the statement crosses the
boundary.

  { "version": "4.x.y",
    "declarations": [ { "name": "Nat.add_zero",
                        "statement": "∀ (n : Nat), n + 0 = n",
                        "type": <expr> } ] }

  <expr> ::= {"kind":"bvar","index":Nat}
           | {"kind":"fvar"|"mvar","name":String}
           | {"kind":"sort","level":String}
           | {"kind":"const","name":String,"levels":[String]}
           | {"kind":"app","fn":<expr>,"arg":<expr>}
           | {"kind":"lam"|"forallE","binderName":String,
              "binderType":<expr>,"body":<expr>}
           | {"kind":"letE","name":String,"type":<expr>,
              "value":<expr>,"body":<expr>}
           | {"kind":"lit","natVal":Nat} | {"kind":"lit","strVal":String}
           | {"kind":"proj","structName":String,"idx":Nat,"expr":<expr>}

Usage. The command writes bare JSON to stdout, so it can be redirected
straight to a file:

  lean -o Export.olean Export.lean
  LEAN_PATH=. lean Dump.lean > dump.json

where `Dump.lean` is `import Export` followed by the `#symbolize_export`
line. Then from Python:

  LeanImporter(Engine(standard())).load(open("dump.json").read())

Verified against Lean 4.34.1: this file compiles, and the declarations in
`tests/terms/fixtures/lean_nat.json` were dumped by it. The six importable
ones round-trip -- the generated `example` lines compile, and fail when a
translation is deliberately corrupted. The JSON schema above is the contract:
if an API detail drifts in a later toolchain, adjust this file (or write your
own dumper) rather than the Python side.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
-/
import Lean

open Lean Meta Elab Command

namespace Symbolize

partial def exprToJson (e : Expr) : MetaM Json := do
  match e with
  | .bvar i =>
      return Json.mkObj [("kind", "bvar"), ("index", toJson i)]
  | .fvar id =>
      return Json.mkObj [("kind", "fvar"), ("name", toJson id.name.toString)]
  | .mvar id =>
      return Json.mkObj [("kind", "mvar"), ("name", toJson id.name.toString)]
  | .sort u =>
      return Json.mkObj [("kind", "sort"), ("level", toJson (toString u))]
  | .const n us =>
      return Json.mkObj
        [("kind", "const"), ("name", toJson n.toString),
         ("levels", Json.arr ((us.map (fun u => toJson (toString u))).toArray))]
  | .app f a =>
      return Json.mkObj
        [("kind", "app"), ("fn", ← exprToJson f), ("arg", ← exprToJson a)]
  | .lam n t b _ =>
      return Json.mkObj
        [("kind", "lam"), ("binderName", toJson n.toString),
         ("binderType", ← exprToJson t), ("body", ← exprToJson b)]
  | .forallE n t b _ =>
      return Json.mkObj
        [("kind", "forallE"), ("binderName", toJson n.toString),
         ("binderType", ← exprToJson t), ("body", ← exprToJson b)]
  | .letE n t v b _ =>
      return Json.mkObj
        [("kind", "letE"), ("name", toJson n.toString),
         ("type", ← exprToJson t), ("value", ← exprToJson v),
         ("body", ← exprToJson b)]
  | .lit (.natVal k) =>
      return Json.mkObj [("kind", "lit"), ("natVal", toJson k)]
  | .lit (.strVal s) =>
      return Json.mkObj [("kind", "lit"), ("strVal", toJson s)]
  | .mdata _ b =>
      exprToJson b
  | .proj s i b =>
      return Json.mkObj
        [("kind", "proj"), ("structName", toJson s.toString),
         ("idx", toJson i), ("expr", ← exprToJson b)]

/-- The statement of one declaration, as JSON. -/
def declJson (name : Name) : MetaM Json := do
  let info ← getConstInfo name
  let type ← instantiateMVars info.type
  return Json.mkObj
    [("name", toJson name.toString),
     ("statement", toJson (toString (← ppExpr type))),
     ("type", ← exprToJson type)]

/-- `#symbolize_export Foo.bar Baz.qux` prints the statements as JSON. -/
elab "#symbolize_export" ids:ident+ : command => do
  let mut decls : Array Json := #[]
  for id in ids do
    let name ← liftCoreM <| realizeGlobalConstNoOverload id
    let j ← liftTermElabM <| declJson name
    decls := decls.push j
  let out := Json.mkObj
    [("version", toJson Lean.versionString), ("declarations", Json.arr decls)]
  logInfo out.pretty

end Symbolize
