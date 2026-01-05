"""
Tests for L methods that delegate to str methods.

This test covers simple delegation methods that were not covered by other tests:
- format_map()
- isidentifier()
- translate()
- maketrans()
- encode()
"""
import unittest
import lstring
from lstring import L


class TestLStrDelegates(unittest.TestCase):
    """Test methods that delegate to str for implementation."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_format_map_basic(self):
        """Test format_map with dict."""
        mapping = {'name': 'World', 'greeting': 'Hello'}
        result = L('{greeting}, {name}!').format_map(mapping)
        expected = '{greeting}, {name}!'.format_map(mapping)
        self.assertEqual(str(result), expected)
    
    def test_format_map_with_missing(self):
        """Test format_map with custom dict that has __missing__."""
        class DefaultDict(dict):
            def __missing__(self, key):
                return f'<{key}>'
        
        mapping = DefaultDict(name='World')
        result = L('{greeting}, {name}!').format_map(mapping)
        expected = '{greeting}, {name}!'.format_map(mapping)
        self.assertEqual(str(result), expected)
        self.assertEqual(str(result), '<greeting>, World!')
    
    def test_isidentifier_valid(self):
        """Test isidentifier with valid identifiers."""
        self.assertTrue(L('hello').isidentifier())
        self.assertTrue(L('_private').isidentifier())
        self.assertTrue(L('var123').isidentifier())
        self.assertTrue(L('αβγ').isidentifier())
    
    def test_isidentifier_invalid(self):
        """Test isidentifier with invalid identifiers."""
        self.assertFalse(L('123var').isidentifier())
        self.assertFalse(L('hello world').isidentifier())
        self.assertFalse(L('hello-world').isidentifier())
        self.assertFalse(L('').isidentifier())
    
    def test_translate_basic(self):
        """Test translate with simple translation table."""
        table = str.maketrans('aeiou', '12345')
        result = L('hello world').translate(table)
        expected = 'hello world'.translate(table)
        self.assertEqual(str(result), expected)
        self.assertIsInstance(result, L)
    
    def test_translate_delete(self):
        """Test translate with character deletion."""
        table = str.maketrans('', '', 'aeiou')
        result = L('hello world').translate(table)
        expected = 'hello world'.translate(table)
        self.assertEqual(str(result), expected)
        self.assertEqual(str(result), 'hll wrld')
    
    def test_translate_unicode(self):
        """Test translate with Unicode characters."""
        table = str.maketrans('αβγ', 'abc')
        result = L('αβγδε').translate(table)
        expected = 'αβγδε'.translate(table)
        self.assertEqual(str(result), expected)
    
    def test_maketrans_two_args(self):
        """Test maketrans with two arguments."""
        table = L.maketrans('abc', '123')
        expected = str.maketrans('abc', '123')
        self.assertEqual(table, expected)
    
    def test_maketrans_three_args(self):
        """Test maketrans with three arguments (delete chars)."""
        table = L.maketrans('abc', '123', 'xyz')
        expected = str.maketrans('abc', '123', 'xyz')
        self.assertEqual(table, expected)
    
    def test_maketrans_dict(self):
        """Test maketrans with dict argument."""
        mapping = {ord('a'): '1', ord('b'): '2'}
        table = L.maketrans(mapping)
        expected = str.maketrans(mapping)
        self.assertEqual(table, expected)
    
    def test_encode_default(self):
        """Test encode with default encoding."""
        result = L('hello').encode()
        expected = 'hello'.encode()
        self.assertEqual(result, expected)
        self.assertEqual(result, b'hello')
    
    def test_encode_utf8(self):
        """Test encode with UTF-8."""
        result = L('привет').encode('utf-8')
        expected = 'привет'.encode('utf-8')
        self.assertEqual(result, expected)
    
    def test_encode_ascii_strict(self):
        """Test encode with ASCII and strict errors."""
        with self.assertRaises(UnicodeEncodeError):
            L('привет').encode('ascii', 'strict')
    
    def test_encode_ascii_ignore(self):
        """Test encode with ASCII and ignore errors."""
        result = L('hello привет').encode('ascii', 'ignore')
        expected = 'hello привет'.encode('ascii', 'ignore')
        self.assertEqual(result, expected)
        self.assertEqual(result, b'hello ')
    
    def test_encode_lazy_string(self):
        """Test encode on lazy string."""
        lazy = L('hello') + L(' world')
        result = lazy.encode()
        expected = b'hello world'
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
