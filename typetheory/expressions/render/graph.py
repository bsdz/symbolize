'''
Created on 10 Jul 2017

@author: bsdz
'''
from graph_tool import Graph
from graph_tool.draw import graph_draw

from .base import Renderer

class GraphToolRendererMixin(object):
    def render_graphtool(self, renderer):  # @UnusedVariable
        raise NotImplementedError()

def _repr_png_(self):
    """For Jupyter/IPython"""
    graph_draw(
        self,
        vertex_text=self.vertex_properties["label"],
        vertex_font_size=18,
        vertex_shape="circle",
        output_size=(200, 200),
        output="test.png"
    )
Graph._repr_png_ = _repr_png_

class GraphToolRenderer(Renderer):
    
    def render(self, expression: "Expression") -> str:
        return expression.render_graphtool(self)
    
    def new_graph(self):
        graph = Graph(directed=True)
        graph.vp["label"] = graph.new_vertex_property("string")
        graph.gp["basevertex"] = graph.new_graph_property("int")
        return graph
    
