'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest
from symbolize.groups import op, G


class GroupTest(unittest.TestCase):


    def test_render(self):
        tex = op.repr_latex()
        self.assertGreater(len(tex), 0)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()