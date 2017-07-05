import unittest

from tests.test_expression import ExpressionTest
from tests.test_arity import ArityTest
from tests.test_definitions import DefinitionsTest

loader = unittest.TestLoader()
suite_list = [loader.loadTestsFromTestCase(cls) for cls in [ArityTest, ExpressionTest, DefinitionsTest]]
unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite_list))