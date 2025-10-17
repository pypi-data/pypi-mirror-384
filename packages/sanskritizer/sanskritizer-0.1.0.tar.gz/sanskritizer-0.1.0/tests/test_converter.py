import unittest
from sanskritizer.converter import to_iast, to_devanagari, pronunciation

class TestSanskritizer(unittest.TestCase):
    def test_known_word(self):
        self.assertEqual(to_iast("peace"), "śānti")
        self.assertEqual(to_devanagari("peace"), "शान्ति")
        self.assertEqual(pronunciation("peace"), "shaanti")

    def test_unknown_word(self):
        self.assertEqual(to_iast("unknown"), "N/A")
        self.assertEqual(to_devanagari("unknown"), "N/A")
        self.assertEqual(pronunciation("unknown"), "N/A")

if __name__ == "__main__":
    unittest.main()