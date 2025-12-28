"""Tests for Pattern.findall, Pattern.finditer, and Pattern.split"""
import lstring
import unittest


class TestFindallFinditerSplit(unittest.TestCase):
    def test_findall_no_groups(self):
        """findall with no capturing groups returns full matches"""
        pat = lstring.re.Pattern(lstring.L(r'\d+'))
        result = pat.findall(lstring.L('a123b456c789'))
        self.assertEqual(len(result), 3)
        self.assertEqual(str(result[0]), '123')
        self.assertEqual(str(result[1]), '456')
        self.assertEqual(str(result[2]), '789')

    def test_findall_one_group(self):
        """findall with one capturing group returns group values"""
        pat = lstring.re.Pattern(lstring.L(r'(\d+)'))
        result = pat.findall(lstring.L('a123b456c789'))
        self.assertEqual(len(result), 3)
        self.assertEqual(str(result[0]), '123')
        self.assertEqual(str(result[1]), '456')
        self.assertEqual(str(result[2]), '789')

    def test_findall_multiple_groups(self):
        """findall with multiple capturing groups returns tuples"""
        pat = lstring.re.Pattern(lstring.L(r'(\w+)=(\d+)'))
        result = pat.findall(lstring.L('a=1, b=2, c=3'))
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], tuple)
        self.assertEqual(len(result[0]), 2)
        self.assertEqual(str(result[0][0]), 'a')
        self.assertEqual(str(result[0][1]), '1')
        self.assertEqual(str(result[1][0]), 'b')
        self.assertEqual(str(result[1][1]), '2')
        self.assertEqual(str(result[2][0]), 'c')
        self.assertEqual(str(result[2][1]), '3')

    def test_findall_empty_matches(self):
        """findall handles empty matches correctly"""
        pat = lstring.re.Pattern(lstring.L(r'\d*'))
        result = pat.findall(lstring.L('a1b2c'))
        # Should find: '', '1', '', '2', '', ''
        self.assertGreaterEqual(len(result), 3)

    def test_findall_with_str(self):
        """findall accepts str argument"""
        pat = lstring.re.Pattern(lstring.L(r'\d+'))
        result = pat.findall('a123b456')
        self.assertEqual(len(result), 2)
        self.assertEqual(str(result[0]), '123')
        self.assertEqual(str(result[1]), '456')

    def test_finditer_basic(self):
        """finditer returns iterator of Match objects"""
        pat = lstring.re.Pattern(lstring.L(r'\d+'))
        result = list(pat.finditer(lstring.L('a123b456c789')))
        self.assertEqual(len(result), 3)
        
        # Check first match
        m1 = result[0]
        self.assertEqual(str(m1.group(0)), '123')
        self.assertEqual(m1.span(), (1, 4))
        
        # Check second match
        m2 = result[1]
        self.assertEqual(str(m2.group(0)), '456')
        self.assertEqual(m2.span(), (5, 8))
        
        # Check third match
        m3 = result[2]
        self.assertEqual(str(m3.group(0)), '789')
        self.assertEqual(m3.span(), (9, 12))

    def test_finditer_with_groups(self):
        """finditer works with capturing groups"""
        pat = lstring.re.Pattern(lstring.L(r'(?<name>\w+)=(?<value>\d+)'))
        result = list(pat.finditer(lstring.L('a=1, b=2')))
        self.assertEqual(len(result), 2)
        
        m1 = result[0]
        self.assertEqual(str(m1.group('name')), 'a')
        self.assertEqual(str(m1.group('value')), '1')
        
        m2 = result[1]
        self.assertEqual(str(m2.group('name')), 'b')
        self.assertEqual(str(m2.group('value')), '2')

    def test_split_basic(self):
        """split splits string by pattern"""
        pat = lstring.re.Pattern(lstring.L(r',\s*'))
        result = pat.split(lstring.L('a, b, c, d'))
        self.assertEqual(len(result), 4)
        self.assertEqual(str(result[0]), 'a')
        self.assertEqual(str(result[1]), 'b')
        self.assertEqual(str(result[2]), 'c')
        self.assertEqual(str(result[3]), 'd')

    def test_split_with_groups(self):
        """split includes capturing groups in result"""
        pat = lstring.re.Pattern(lstring.L(r'([,;])'))
        result = pat.split(lstring.L('a,b;c'))
        self.assertEqual(len(result), 5)
        self.assertEqual(str(result[0]), 'a')
        self.assertEqual(str(result[1]), ',')
        self.assertEqual(str(result[2]), 'b')
        self.assertEqual(str(result[3]), ';')
        self.assertEqual(str(result[4]), 'c')

    def test_split_maxsplit(self):
        """split respects maxsplit parameter"""
        pat = lstring.re.Pattern(lstring.L(r','))
        result = pat.split(lstring.L('a,b,c,d'), 2)
        self.assertEqual(len(result), 3)
        self.assertEqual(str(result[0]), 'a')
        self.assertEqual(str(result[1]), 'b')
        self.assertEqual(str(result[2]), 'c,d')

    def test_split_no_match(self):
        """split returns original string if no match"""
        pat = lstring.re.Pattern(lstring.L(r'xyz'))
        result = pat.split(lstring.L('abc'))
        self.assertEqual(len(result), 1)
        self.assertEqual(str(result[0]), 'abc')

    def test_split_empty_parts(self):
        """split handles empty parts correctly"""
        pat = lstring.re.Pattern(lstring.L(r','))
        result = pat.split(lstring.L(',a,,b,'))
        self.assertEqual(len(result), 5)
        self.assertEqual(str(result[0]), '')
        self.assertEqual(str(result[1]), 'a')
        self.assertEqual(str(result[2]), '')
        self.assertEqual(str(result[3]), 'b')
        self.assertEqual(str(result[4]), '')

    def test_split_with_str(self):
        """split accepts str argument"""
        pat = lstring.re.Pattern(lstring.L(r','))
        result = pat.split('a,b,c')
        self.assertEqual(len(result), 3)
        self.assertEqual(str(result[0]), 'a')
        self.assertEqual(str(result[1]), 'b')
        self.assertEqual(str(result[2]), 'c')


if __name__ == '__main__':
    unittest.main()

