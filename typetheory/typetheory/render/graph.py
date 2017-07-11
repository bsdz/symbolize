'''
Created on 10 Jul 2017

@author: bsdz
'''
from graph_tool.all import Graph, graph_union

from .base import Renderer


class GraphRenderer(Renderer):
    def render(self) -> Graph:
        graph = Graph(directed=True)
        vprop = graph.new_vertex_property("string")
        base_vertex = graph.add_vertex()
        vprop[base_vertex] = self.expression.baserepr
        graph.vertex_properties["name"] = vprop

        if
        for e in self.expression.applications:
            subgraph = GraphRenderer(e).render()
            graph = graph_union(graph, subgraph)
            graph.add_edge(base_vertex, subgraph.vertex(0))

        if self.expression.abstractions:
            lambda_vertex = graph.add_vertex()
            vprop[lambda_vertex] = "lambda"
            graph.vertex_properties["name"] = vprop
            graph.add_edge(lambda_vertex, base_vertex)
            for e in self.expression.abstractions:
                subgraph = GraphRenderer(e).render()
                graph = graph_union(graph, subgraph)
                graph.add_edge(lambda_vertex, subgraph.vertex(0))

        return graph
