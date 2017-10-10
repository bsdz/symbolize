'''
symbolize - Mathematical Symbol Engine
Copyright (C) 2017  Blair Azzopardi
Distributed under the terms of the GNU General Public License (GPL v3)
'''

import unittest
import os

def main():
    loader = unittest.TestLoader()
    this_dir = os.path.dirname(__file__)
    suite_list = loader.discover(start_dir=this_dir)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite_list))

if __name__ == "__main__":
    main()