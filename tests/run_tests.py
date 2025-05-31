import unittest
import sys
import os

# Add the parent directory (project root) to sys.path to allow imports like 'from python_cli.settings'
# This is necessary if run_tests.py is executed as a script from within the tests directory
# or if the python_cli package itself isn't installed/in PYTHONPATH.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if __name__ == '__main__':
    # Discover tests in the current directory (python_cli/tests)
    # Test files should be named test_*.py
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir='.', pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Exit with a non-zero status code if any tests failed
    if not result.wasSuccessful():
        sys.exit(1)
