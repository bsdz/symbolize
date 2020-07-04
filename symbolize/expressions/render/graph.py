"""
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
"""

from ..expression import Expression
from .base import Renderer


class GraphToolRendererMixin:
    def render_graphtool(self, renderer):  # @UnusedVariable
        raise NotImplementedError()


def _repr_png_(self):
    """For Jupyter/IPython"""
    from graph_tool.draw import graph_draw

    graph_draw(
        self,
        vertex_text=self.vertex_properties["label"],
        vertex_font_size=18,
        vertex_shape="circle",
        output_size=(200, 200),
        output="test.png",
    )


class GraphToolRenderer(Renderer):
    def render(self, expression: Expression) -> str:
        return expression.render_graphtool(self)

    def new_graph(self):
        from graph_tool import Graph

        Graph._repr_png_ = _repr_png_
        graph = Graph(directed=True)
        graph.vp["label"] = graph.new_vertex_property("string")
        graph.gp["basevertex"] = graph.new_graph_property("int")
        return graph
