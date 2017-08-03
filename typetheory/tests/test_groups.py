'''
Created on 17 Jul 2017

@author: bsdz
'''
import unittest
from typetheory.groups import op, G


class GroupTest(unittest.TestCase):


    def test_render(self):
        tex = op.render_latex()
        self.assertGreater(len(tex), 0)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()