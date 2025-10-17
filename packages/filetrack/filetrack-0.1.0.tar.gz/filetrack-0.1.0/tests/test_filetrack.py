import sys
import os.path
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import filetrack  # noqa: linter (pycodestyle) should not lint this line.


class test_filetrack(unittest.TestCase):
    """filetrack unittest"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_version(self):
        self.assertIsInstance(filetrack.__version__, str)


if __name__ == "__main__":
    unittest.main(verbosity=2, exit=False)
