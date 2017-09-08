import unittest

from symbolize.expressions import Symbol
from symbolize.definitions.operators import plus

package_graphtool_installed = False
try:
    from graph_tool import Graph
    package_graphtool_installed = True
except Exception:
    pass

class GraphToolRenderTest(unittest.TestCase):

    @unittest.skipIf(not package_graphtool_installed, "graphtool not installed")
    def test_render_graph(self):
        x = Symbol('x')
        y = Symbol('y')
        expr = plus(x,plus(x, y)).abstract(y)
        graph = expr.repr_graphtool()
        self.assertIsNotNone(graph)

if __name__ == '__main__':
    unittest.main()
