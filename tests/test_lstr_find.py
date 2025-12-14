import unittest
import lstring


class TestLStrFind(unittest.TestCase):
    """Tests for `_lstr.find` to match Python str.find semantics."""

    def setUp(self):
        self.s = '123'
        self.l = lstring._lstr(self.s)

    def test_empty_substring_various_starts(self):
        # str.find semantics with empty substring
        self.assertEqual(self.s.find(''), 0)
        self.assertEqual(self.s.find('', -1), 2)
        self.assertEqual(self.s.find('', None), 0)
        self.assertEqual(self.s.find('', 5), -1)
        self.assertEqual(self.s.find('', 3), 3)

        # same behavior when calling _lstr.find with Python str
        self.assertEqual(self.l.find(''), 0)
        self.assertEqual(self.l.find('', -1), 2)
        self.assertEqual(self.l.find('', None), 0)
        self.assertEqual(self.l.find('', 5), -1)
        self.assertEqual(self.l.find('', 3), 3)

    def test_search_single_char(self):
        # searching for '2'
        self.assertEqual(self.s.find('2'), 1)
        self.assertEqual(self.s.find('2', -1), -1)
        self.assertEqual(self.s.find('2', -3), 1)
        self.assertEqual(self.s.find('2', -5), 1)

        # same when sub is _lstr
        sub_l = lstring._lstr('2')
        self.assertEqual(self.l.find(sub_l), 1)
        self.assertEqual(self.l.find(sub_l, -1), -1)
        self.assertEqual(self.l.find(sub_l, -3), 1)
        self.assertEqual(self.l.find(sub_l, -5), 1)


if __name__ == '__main__':
    unittest.main()
