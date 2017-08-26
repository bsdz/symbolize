import unittest

from tests.expressions.test_expression import ExpressionTest
from tests.expressions.test_arity import ArityTest
from tests.expressions.test_renderer import RendererTest
from tests.definitions.test_definitions import DefinitionsTest
from tests.logic.test_proposition import PropositionTest
from tests.expressions.test_render_graphtool import GraphToolRenderTest


def main():
    classes = [ArityTest, ExpressionTest, DefinitionsTest, RendererTest, PropositionTest]
    
    loader = unittest.TestLoader()
    suite_list = [loader.loadTestsFromTestCase(cls) for cls in classes]
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite_list))


if __name__ == "__main__":
    unittest.main()