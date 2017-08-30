import unittest
import inspect

from tests.expressions.test_expression import ExpressionTest, ExpressionCombinationTest
from tests.expressions.test_arity import ArityTest
from tests.expressions.test_renderer import RendererTest
from tests.definitions.test_definitions import DefinitionsTest
from tests.logic.test_proposition import PropositionTest
from tests.expressions.test_render_graphtool import GraphToolRenderTest


def main():
    loader = unittest.TestLoader()
    suite_list = [loader.loadTestsFromTestCase(cls) for name,cls in globals().items() if inspect.isclass(cls) and issubclass(cls, unittest.TestCase)]
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite_list))


if __name__ == "__main__":
    main()