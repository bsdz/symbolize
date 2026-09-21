"""Graph renderer: a term as a tree of labelled vertices, in Graphviz DOT
form, or as a ``graph_tool.Graph`` when graph-tool is installed.

symbolize - Mathematical Symbol Engine
Copyright (C) 2026  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from __future__ import annotations

from typing import List, Tuple

from ..term import Abs, App, Bound, Comb, Const, Sel, Term, Var, _fresh_names
from .notation import lookup


def tree(term: Term) -> Tuple[List[str], List[Tuple[int, int]]]:
    """Vertex labels and parent→child edges of ``term``'s syntax tree.
    Applications are drawn with the head as the parent of its arguments."""
    labels: List[str] = []
    edges: List[Tuple[int, int]] = []

    def add(label: str) -> int:
        labels.append(label)
        return len(labels) - 1

    def visit(t: Term, names: List[str]) -> int:
        if isinstance(t, Var):
            return add(t.name)
        if isinstance(t, Const):
            return add(lookup(t).symbol("unicode", t.name))
        if isinstance(t, Bound):
            return add(names[t.index] if t.index < len(names) else "#%d" % t.index)
        if isinstance(t, App):
            v = visit(t.fn, names)
            for a in t.args:
                edges.append((v, visit(a, names)))
            return v
        if isinstance(t, Abs):
            inner = _fresh_names(t.hints, names, set())
            v = add("λ" if False else "(%s)" % ", ".join(inner))
            edges.append((v, visit(t.body, list(inner) + names)))
            return v
        if isinstance(t, Comb):
            v = add(",")
            for i in t.items:
                edges.append((v, visit(i, names)))
            return v
        if isinstance(t, Sel):
            v = add(".%d" % t.index)
            edges.append((v, visit(t.term, names)))
            return v
        raise TypeError("Cannot render %r" % (t,))

    visit(term, [])
    return labels, edges


def dot(term: Term) -> str:
    """Graphviz DOT source for the syntax tree of ``term``."""
    labels, edges = tree(term)
    lines = ["digraph term {", "  node [shape=circle];"]
    for i, label in enumerate(labels):
        lines.append('  n%d [label="%s"];' % (i, label.replace('"', '\\"')))
    for a, b in edges:
        lines.append("  n%d -> n%d;" % (a, b))
    lines.append("}")
    return "\n".join(lines)


def graph_tool(term: Term):
    """The syntax tree as a ``graph_tool.Graph`` with a ``label`` vertex
    property and a ``basevertex`` graph property (the root)."""
    from graph_tool import Graph  # optional dependency

    labels, edges = tree(term)
    g = Graph(directed=True)
    g.vp["label"] = g.new_vertex_property("string")
    g.gp["basevertex"] = g.new_graph_property("int")
    vertices = []
    for label in labels:
        v = g.add_vertex()
        g.vp["label"][v] = label
        vertices.append(v)
    for a, b in edges:
        g.add_edge(vertices[a], vertices[b])
    g.gp["basevertex"] = int(vertices[0]) if vertices else 0
    return g
