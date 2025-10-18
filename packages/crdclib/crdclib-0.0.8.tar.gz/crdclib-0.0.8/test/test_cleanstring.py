import unittest
from crdclib import crdclib as cl


class TestCleanString(unittest.TestCase):

    def test_fullClean(self):
        teststring = "This is # Test\t\r\n!@#$%^&*()"
        self.assertEqual(cl.cleanString(teststring), "ThisisTest")
        self.assertEqual(cl.cleanString(teststring, False), "ThisisTest")
        self.assertEqual(cl.cleanString(teststring, True), "This is # Test!@#$%^&*()")


if __name__ == "__main__":
    unittest.main(verbosity=2)
