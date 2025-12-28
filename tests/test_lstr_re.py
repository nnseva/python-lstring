import unittest
import lstring
import lstring.re


class TestLStrRe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.orig = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls.orig)

    def test_pattern_match_from_start(self):
        p = lstring.re.Pattern(r"\d+")
        m = p.match("123abc")
        self.assertIsNotNone(m)
        m = p.match("abc123")
        self.assertIsNone(m)

    def test_pattern_match_str_and_L(self):
        p = lstring.re.Pattern("hello")
        # Test with str
        m1 = p.match("hello world")
        self.assertIsNotNone(m1)
        # Test with L
        m2 = p.match(lstring.L("hello world"))
        self.assertIsNotNone(m2)

    def test_pattern_search_anywhere(self):
        p = lstring.re.Pattern(r"\d+")
        m = p.search("abc123def")
        self.assertIsNotNone(m)
        m = p.search("123abc")
        self.assertIsNotNone(m)
        m = p.search("abcdef")
        self.assertIsNone(m)

    def test_pattern_search_vs_match(self):
        p = lstring.re.Pattern(r"\d+")
        # search finds in middle
        self.assertIsNotNone(p.search("abc123"))
        # match requires start
        self.assertIsNone(p.match("abc123"))
        # both find at start
        self.assertIsNotNone(p.match("123abc"))
        self.assertIsNotNone(p.search("123abc"))

    def test_invalid_pattern_type(self):
        with self.assertRaises(TypeError):
            lstring.re.Pattern(123)

    def test_search_with_pos(self):
        p = lstring.re.Pattern(r"\d+")
        text = lstring.L("abc123def456")
        # Normal search finds first match
        m = p.search(text)
        self.assertIsNotNone(m)
        # Search from pos=3 skips "abc" and finds "123"
        m = p.search(text, 3)
        self.assertIsNotNone(m)
        # Search from pos=6 skips "123" and finds "456"
        m = p.search(text, 6)
        self.assertIsNotNone(m)
        # Search from pos=12 finds nothing
        m = p.search(text, 12)
        self.assertIsNone(m)

    def test_search_with_endpos(self):
        p = lstring.re.Pattern(r"\d+")
        text = lstring.L("abc123def456")
        # Search in range [0, 6) finds "123" only
        m = p.search(text, 0, 6)
        self.assertIsNotNone(m)
        # Search in range [0, 3) finds nothing (only "abc")
        m = p.search(text, 0, 3)
        self.assertIsNone(m)
        # Search in range [6, 12) finds "456"
        m = p.search(text, 6, 12)
        self.assertIsNotNone(m)

    def test_match_with_pos(self):
        p = lstring.re.Pattern(r"\d+")
        text = lstring.L("abc123def456")
        # Match from start fails (starts with "abc")
        m = p.match(text)
        self.assertIsNone(m)
        # Match from pos=3 succeeds ("123def456" starts with digits)
        m = p.match(text, 3)
        self.assertIsNotNone(m)
        # Match from pos=6 fails ("def456" starts with letters)
        m = p.match(text, 6)
        self.assertIsNone(m)
        # Match from pos=9 succeeds ("456" starts with digits)
        m = p.match(text, 9)
        self.assertIsNotNone(m)

    def test_match_with_endpos(self):
        p = lstring.re.Pattern(r"\d+")
        text = lstring.L("123456")
        # Match in range [0, 6) succeeds (full string)
        m = p.match(text, 0, 6)
        self.assertIsNotNone(m)
        # Match in range [0, 3) succeeds (just "123")
        m = p.match(text, 0, 3)
        self.assertIsNotNone(m)
        # Match from pos=2 in range [2, 6) succeeds ("3456")
        m = p.match(text, 2, 6)
        self.assertIsNotNone(m)

    def test_pos_endpos_clamping(self):
        p = lstring.re.Pattern(r".")
        text = lstring.L("hello")
        # pos beyond length is clamped
        m = p.search(text, 100)
        self.assertIsNone(m)
        # endpos beyond length is clamped
        m = p.search(text, 0, 100)
        self.assertIsNotNone(m)
        # endpos < pos is adjusted to endpos = pos
        m = p.search(text, 3, 1)
        self.assertIsNone(m)

    def test_pos_endpos_with_str(self):
        p = lstring.re.Pattern(r"\w+")
        # Test that pos/endpos work with str input (converted to L internally)
        m = p.search("abc123def", 3)
        self.assertIsNotNone(m)
        m = p.search("abc123def", 0, 3)
        self.assertIsNotNone(m)

    def test_fullmatch_basic(self):
        p = lstring.re.Pattern(r"\d+")
        # fullmatch requires entire string to match
        m = p.fullmatch("123")
        self.assertIsNotNone(m)
        # Partial match fails
        m = p.fullmatch("123abc")
        self.assertIsNone(m)
        m = p.fullmatch("abc123")
        self.assertIsNone(m)

    def test_fullmatch_vs_match_vs_search(self):
        p = lstring.re.Pattern(r"\d+")
        
        # All three succeed on exact match
        self.assertIsNotNone(p.fullmatch("123"))
        self.assertIsNotNone(p.match("123"))
        self.assertIsNotNone(p.search("123"))
        
        # Only match and search succeed when pattern at start
        self.assertIsNone(p.fullmatch("123abc"))
        self.assertIsNotNone(p.match("123abc"))
        self.assertIsNotNone(p.search("123abc"))
        
        # Only search succeeds when pattern not at start
        self.assertIsNone(p.fullmatch("abc123"))
        self.assertIsNone(p.match("abc123"))
        self.assertIsNotNone(p.search("abc123"))

    def test_fullmatch_with_pos_endpos(self):
        p = lstring.re.Pattern(r"\d+")
        text = lstring.L("abc123def")
        
        # fullmatch in range [3, 6) matches "123"
        m = p.fullmatch(text, 3, 6)
        self.assertIsNotNone(m)
        
        # fullmatch in range [0, 6) fails (starts with "abc")
        m = p.fullmatch(text, 0, 6)
        self.assertIsNone(m)
        
        # fullmatch in range [3, 9) fails (ends with "def")
        m = p.fullmatch(text, 3, 9)
        self.assertIsNone(m)

    def test_match_group_basic(self):
        p = lstring.re.Pattern(r'(\d+)-(\w+)')
        m = p.match('123-abc')
        
        # group() and group(0) return full match
        g0a = m.group()
        g0b = m.group(0)
        self.assertEqual(str(g0a), '123-abc')
        self.assertEqual(str(g0b), '123-abc')
        
        # group(1) and group(2) return capturing groups
        g1 = m.group(1)
        g2 = m.group(2)
        self.assertEqual(str(g1), '123')
        self.assertEqual(str(g2), 'abc')
        
    def test_match_group_multiple(self):
        p = lstring.re.Pattern(r'(\d+)-(\w+)')
        m = p.match('456-xyz')
        
        # group(1, 2) returns tuple
        result = m.group(1, 2)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(str(result[0]), '456')
        self.assertEqual(str(result[1]), 'xyz')

    def test_match_groups(self):
        p = lstring.re.Pattern(r'(\d+)-(\w+)')
        m = p.match('789-qwe')
        
        # groups() returns all capturing groups (excluding group 0)
        result = m.groups()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertEqual(str(result[0]), '789')
        self.assertEqual(str(result[1]), 'qwe')

    def test_match_optional_groups(self):
        p = lstring.re.Pattern(r'(\d+)(-(\w+))?')
        
        # Match with optional group present
        m1 = p.match('123-abc')
        self.assertEqual(str(m1.group(1)), '123')
        self.assertEqual(str(m1.group(2)), '-abc')
        self.assertEqual(str(m1.group(3)), 'abc')
        
        # Match with optional group absent
        m2 = p.match('456')
        self.assertEqual(str(m2.group(1)), '456')
        self.assertIsNone(m2.group(2))
        self.assertIsNone(m2.group(3))
        
        # groups() with default
        groups = m2.groups()
        self.assertEqual(len(groups), 3)
        self.assertEqual(str(groups[0]), '456')
        self.assertIsNone(groups[1])
        self.assertIsNone(groups[2])

    def test_match_group_with_L(self):
        p = lstring.re.Pattern(r'(\w+):(\d+)')
        text = lstring.L("hello:42")
        m = p.match(text)
        
        # Groups should work with L input
        self.assertEqual(str(m.group(1)), 'hello')
        self.assertEqual(str(m.group(2)), '42')
        
        groups = m.groups()
        self.assertEqual(str(groups[0]), 'hello')
        self.assertEqual(str(groups[1]), '42')

    def test_module_compile(self):
        # Test lstring.re.compile function
        p = lstring.re.compile(r'\d+')
        self.assertIsInstance(p, type(lstring.re.Pattern(r'test')))
        
        m = p.match('123abc')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group()), '123')

    def test_module_match(self):
        # Test lstring.re.match function
        m = lstring.re.match(r'\d+', '456def')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group()), '456')
        
        # Should not match if pattern not at start
        m = lstring.re.match(r'\d+', 'abc456')
        self.assertIsNone(m)

    def test_module_search(self):
        # Test lstring.re.search function
        m = lstring.re.search(r'\d+', 'abc789xyz')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group()), '789')
        
        # Works with L
        m = lstring.re.search(r'\d+', lstring.L('test123'))
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group()), '123')

    def test_module_fullmatch(self):
        # Test lstring.re.fullmatch function
        m = lstring.re.fullmatch(r'\d+', '999')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group()), '999')
        
        # Should not match partial
        m = lstring.re.fullmatch(r'\d+', '999abc')
        self.assertIsNone(m)

    def test_module_functions_with_groups(self):
        # Test module functions with capturing groups
        m = lstring.re.match(r'(\w+)-(\d+)', 'hello-123')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group(1)), 'hello')
        self.assertEqual(str(m.group(2)), '123')
        
        groups = m.groups()
        self.assertEqual(len(groups), 2)

    def test_named_groups_boost_syntax(self):
        # Test named groups using Boost syntax: (?<name>...)
        p = lstring.re.Pattern(r'(?<first>\w+)-(?<second>\d+)')
        m = p.match('hello-123')
        self.assertIsNotNone(m)
        
        # Access by index
        self.assertEqual(str(m.group(0)), 'hello-123')
        self.assertEqual(str(m.group(1)), 'hello')
        self.assertEqual(str(m.group(2)), '123')
        
        # Access by name (str)
        self.assertEqual(str(m.group('first')), 'hello')
        self.assertEqual(str(m.group('second')), '123')
        
        # Access by name (L)
        self.assertEqual(str(m.group(lstring.L('first'))), 'hello')
        self.assertEqual(str(m.group(lstring.L('second'))), '123')

    def test_named_groups_multiple_args(self):
        # Test multiple group arguments with names
        p = lstring.re.Pattern(r'(?<a>\d+)(?<b>[a-z]+)(?<c>\d+)')
        m = p.match('123abc456')
        self.assertIsNotNone(m)
        
        # Mix of index and name access
        result = m.group(0, 'a', 2, 'c')
        self.assertEqual(len(result), 4)
        self.assertEqual(str(result[0]), '123abc456')
        self.assertEqual(str(result[1]), '123')
        self.assertEqual(str(result[2]), 'abc')
        self.assertEqual(str(result[3]), '456')

    def test_named_groups_unmatched(self):
        # Test that unmatched named groups return None
        p = lstring.re.Pattern(r'(?<opt>\d+)?(?<req>\w+)')
        m = p.match('hello')
        self.assertIsNotNone(m)
        
        # Optional group not matched
        self.assertIsNone(m.group('opt'))
        self.assertIsNone(m.group(1))
        
        # Required group matched
        self.assertEqual(str(m.group('req')), 'hello')
        self.assertEqual(str(m.group(2)), 'hello')

    def test_named_groups_invalid_name(self):
        # Test error handling for invalid group names
        p = lstring.re.Pattern(r'(?<valid>\d+)')
        m = p.match('123')
        self.assertIsNotNone(m)
        
        # Valid name works
        self.assertEqual(str(m.group('valid')), '123')
        
        # Invalid type should raise TypeError
        with self.assertRaises(TypeError):
            m.group([1, 2, 3])
        
        with self.assertRaises(TypeError):
            m.group({})

    def test_named_groups_module_functions(self):
        # Test named groups work with module-level functions
        m = lstring.re.search(r'name:(?<value>\w+)', 'name:John age:30')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group('value')), 'John')
        
        m = lstring.re.fullmatch(r'(?<x>\d+)\.(?<y>\d+)', '123.456')
        self.assertIsNotNone(m)
        self.assertEqual(str(m.group('x')), '123')
        self.assertEqual(str(m.group('y')), '456')

    def test_match_getitem_by_index(self):
        # Test Match[index] syntax
        p = lstring.re.Pattern(r'(\w+)-(\d+)')
        m = p.match('hello-123')
        self.assertIsNotNone(m)
        
        # Access by index
        self.assertEqual(str(m[0]), 'hello-123')
        self.assertEqual(str(m[1]), 'hello')
        self.assertEqual(str(m[2]), '123')
        
        # Should be equivalent to group()
        self.assertEqual(str(m[0]), str(m.group(0)))
        self.assertEqual(str(m[1]), str(m.group(1)))
        self.assertEqual(str(m[2]), str(m.group(2)))

    def test_match_getitem_by_name(self):
        # Test Match['name'] syntax
        p = lstring.re.Pattern(r'(?<word>\w+)-(?<num>\d+)')
        m = p.match('test-456')
        self.assertIsNotNone(m)
        
        # Access by name (str)
        self.assertEqual(str(m['word']), 'test')
        self.assertEqual(str(m['num']), '456')
        
        # Access by name (L)
        self.assertEqual(str(m[lstring.L('word')]), 'test')
        self.assertEqual(str(m[lstring.L('num')]), '456')
        
        # Should be equivalent to group()
        self.assertEqual(str(m['word']), str(m.group('word')))
        self.assertEqual(str(m['num']), str(m.group('num')))

    def test_match_getitem_unmatched(self):
        # Test __getitem__ returns None for unmatched groups
        p = lstring.re.Pattern(r'(?<opt>\d+)?(?<req>\w+)')
        m = p.match('abc')
        self.assertIsNotNone(m)
        
        # Unmatched optional group
        self.assertIsNone(m[1])
        self.assertIsNone(m['opt'])
        
        # Matched required group
        self.assertEqual(str(m[2]), 'abc')
        self.assertEqual(str(m['req']), 'abc')

    def test_match_getitem_errors(self):
        # Test __getitem__ error handling
        p = lstring.re.Pattern(r'(?<valid>\d+)')
        m = p.match('123')
        self.assertIsNotNone(m)
        
        # Out of range index
        with self.assertRaises(IndexError):
            _ = m[5]
        
        # Invalid type
        with self.assertRaises(TypeError):
            _ = m[[1, 2]]


if __name__ == "__main__":
    unittest.main()
