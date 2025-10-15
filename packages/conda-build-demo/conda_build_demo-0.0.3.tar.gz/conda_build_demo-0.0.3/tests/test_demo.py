import unittest
from conda_build_demo import Demo

class TestDemo(unittest.TestCase):
    def test_version(self):
        demo = Demo()
        self.assertGreaterEqual(len(demo.version()), 5, "Version property should be longer than five characters")

if __name__ == "__main__":
    unittest.main()
