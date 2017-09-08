import unittest
import os

def main():
    loader = unittest.TestLoader()
    this_dir = os.path.dirname(__file__)
    suite_list = loader.discover(start_dir=this_dir)
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(suite_list))

if __name__ == "__main__":
    main()