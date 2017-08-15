'''
Created on 10 Jul 2017

@author: bsdz
'''
from graph_tool import Graph
from graph_tool.generation import graph_union
from graph_tool.draw import graph_draw


from .base import Renderer


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

class GraphRenderer(Renderer):
    def render(self, expression: "Expression") -> Graph:
        graph = Graph(directed=True)
        graph.vp["label"] = graph.new_vertex_property("string")
        base_vertex = graph.add_vertex()
        graph.gp["basevertex"] = graph.new_graph_property("int", base_vertex)
        graph.vp["label"][base_vertex] = expression.baserepr
        
        if hasattr(expression, "applications"):
            for e in expression.applications:
                subgraph = self.render(e)
                intersection_map = subgraph.new_vertex_property("int")
                
                subgraph_placeholder_vertex = graph.add_vertex()
                graph.add_edge(base_vertex, subgraph_placeholder_vertex)
    
                for v in subgraph.vertices():
                    intersection_map[v] = -1
                intersection_map[subgraph.vertex(subgraph.gp["basevertex"])] = subgraph_placeholder_vertex
                 
                graph, combined_props = graph_union(graph, subgraph,
                       props=[(graph.vp["label"], subgraph.vp["label"])],
                       intersection=intersection_map)
                graph.vp["label"] = combined_props[0]
                graph.gp["basevertex"] = graph.new_graph_property("int", base_vertex)


        if hasattr(expression, "abstractions") and expression.abstractions:
            lambda_vertex = graph.add_vertex()
            graph.gp["basevertex"] = graph.new_graph_property("int", lambda_vertex)
            graph.vp["label"][lambda_vertex] = "λ"
            graph.add_edge(base_vertex, lambda_vertex)
            
            for e in expression.abstractions:
                subgraph = self.render(e)
                intersection_map = subgraph.new_vertex_property("int")
                 
                subgraph_placeholder_vertex = graph.add_vertex()
                graph.add_edge(lambda_vertex, subgraph_placeholder_vertex)
                 
                for v in subgraph.vertices():
                    intersection_map[v] = -1
                intersection_map[subgraph.vertex(subgraph.gp["basevertex"])] = subgraph_placeholder_vertex
                 
                graph, combined_props = graph_union(graph, subgraph,
                       props=[(graph.vp["label"], subgraph.vp["label"])],
                       intersection=intersection_map)
                graph.vp["label"] = combined_props[0]
                graph.gp["basevertex"] = graph.new_graph_property("int", lambda_vertex)

        return graph
