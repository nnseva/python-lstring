import unittest
import lstring
from lstring import L


class TestLStringJoin(unittest.TestCase):
    """Test cases for L.join() method"""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_join_with_separator(self):
        """Test join with non-empty separator"""
        result = L(', ').join(['a', 'b', 'c'])
        self.assertEqual(str(result), 'a, b, c')
        self.assertIsInstance(result, L)
    
    def test_join_with_empty_separator(self):
        """Test join with empty separator"""
        result = L('').join(['hello', 'world'])
        self.assertEqual(str(result), 'helloworld')
        self.assertIsInstance(result, L)
    
    def test_join_single_element(self):
        """Test join with single element"""
        result = L(', ').join(['single'])
        self.assertEqual(str(result), 'single')
        self.assertIsInstance(result, L)
    
    def test_join_empty_list(self):
        """Test join with empty list"""
        result = L(', ').join([])
        self.assertEqual(str(result), '')
        self.assertIsInstance(result, L)
    
    def test_join_with_lstring_elements(self):
        """Test join with L instances as elements"""
        result = L(' | ').join([L('one'), L('two'), L('three')])
        self.assertEqual(str(result), 'one | two | three')
        self.assertIsInstance(result, L)
    
    def test_join_with_iterator(self):
        """Test join with iterator (generator)"""
        result = L('-').join(str(i) for i in range(5))
        self.assertEqual(str(result), '0-1-2-3-4')
        self.assertIsInstance(result, L)
    
    def test_join_with_tuple(self):
        """Test join with tuple"""
        result = L(' ').join(('hello', 'world', 'test'))
        self.assertEqual(str(result), 'hello world test')
        self.assertIsInstance(result, L)
    
    def test_join_rejects_numbers(self):
        """Test that join rejects numeric values"""
        with self.assertRaises(TypeError) as cm:
            L(', ').join([1, 2, 3, 4, 5])
        self.assertIn('expected str or L instance', str(cm.exception))
        self.assertIn('int found', str(cm.exception))
    
    def test_join_rejects_mixed_types(self):
        """Test that join rejects mixed types with non-string/L types"""
        with self.assertRaises(TypeError) as cm:
            L(' - ').join(['text', 42, L('lstring'), 3.14])
        self.assertIn('sequence item 1', str(cm.exception))
        self.assertIn('expected str or L instance', str(cm.exception))
        self.assertIn('int found', str(cm.exception))
    
    def test_join_accepts_mixed_str_and_L(self):
        """Test that join accepts mixed str and L instances"""
        result = L(' - ').join(['text', L('lstring'), 'more'])
        self.assertEqual(str(result), 'text - lstring - more')
        self.assertIsInstance(result, L)
    
    def test_join_two_elements(self):
        """Test join with exactly two elements"""
        result = L(' and ').join(['first', 'second'])
        self.assertEqual(str(result), 'first and second')
        self.assertIsInstance(result, L)
    
    def test_join_multichar_separator(self):
        """Test join with multi-character separator"""
        result = L(' <=> ').join(['a', 'b', 'c', 'd'])
        self.assertEqual(str(result), 'a <=> b <=> c <=> d')
        self.assertIsInstance(result, L)
    
    def test_join_empty_strings(self):
        """Test join with empty string elements"""
        result = L(', ').join(['', '', ''])
        self.assertEqual(str(result), ', , ')
        self.assertIsInstance(result, L)
    
    def test_join_unicode(self):
        """Test join with unicode strings"""
        result = L(' ').join(['привет', 'мир', '世界'])
        self.assertEqual(str(result), 'привет мир 世界')
        self.assertIsInstance(result, L)
    
    def test_join_large_list(self):
        """Test join with large list to verify balanced tree construction"""
        items = [f'item{i}' for i in range(100)]
        result = L(',').join(items)
        expected = ','.join(items)
        self.assertEqual(str(result), expected)
        self.assertIsInstance(result, L)
    
    def test_join_preserves_lazy_evaluation(self):
        """Test that join preserves lazy evaluation by using L elements"""
        l1 = L('hello')
        l2 = L('world')
        l3 = L('test')
        result = L(' ').join([l1, l2, l3])
        self.assertEqual(str(result), 'hello world test')
        self.assertIsInstance(result, L)
    
    def test_join_empty_separator_with_empty_list(self):
        """Test join with empty separator and empty list"""
        result = L('').join([])
        self.assertEqual(str(result), '')
        self.assertIsInstance(result, L)
    
    def test_join_single_element_no_separator_added(self):
        """Test that separator is not added when joining single element"""
        result = L('|||').join(['only'])
        self.assertEqual(str(result), 'only')
        # Verify no separator was added
        self.assertNotIn('|||', str(result))
    
    def test_join_comparison_with_str_join(self):
        """Test that join produces same result as str.join"""
        items = ['alpha', 'beta', 'gamma', 'delta']
        separator = ' :: '
        
        lstring_result = str(L(separator).join(items))
        str_result = separator.join(items)
        
        self.assertEqual(lstring_result, str_result)
    
    def test_join_power_of_two_elements(self):
        """Test join with power-of-two number of elements (optimal for binary tree)"""
        items = [f'e{i}' for i in range(8)]  # 8 = 2^3
        result = L('-').join(items)
        expected = '-'.join(items)
        self.assertEqual(str(result), expected)
    
    def test_join_non_power_of_two_elements(self):
        """Test join with non-power-of-two number of elements"""
        items = [f'e{i}' for i in range(7)]  # 7 is not power of 2
        result = L('-').join(items)
        expected = '-'.join(items)
        self.assertEqual(str(result), expected)


if __name__ == '__main__':
    unittest.main()
