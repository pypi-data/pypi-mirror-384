import sys
import os
import unittest

# Add the build directory to the Python path
script_dir = os.path.dirname(os.path.realpath(__file__))
build_dir = os.path.abspath(os.path.join(script_dir, '..', '..', 'build', 'Debug'))
sys.path.insert(0, build_dir)

# Discover and run the tests
loader = unittest.TestLoader()
suite = loader.loadTestsFromName('tests.test_graph')
runner = unittest.TextTestRunner()
runner.run(suite)
