"""
Tests for L.partition() and L.rpartition() methods
"""

import unittest
from lstring import L


class TestPartition(unittest.TestCase):
    """Test L.partition() method"""
    
    def test_partition_basic(self):
        """Basic partition with separator found."""
        result = L('hello:world').partition(':')
        self.assertEqual(result, (L('hello'), L(':'), L('world')))
    
    def test_partition_separator_not_found(self):
        """Partition when separator is not found."""
        result = L('hello').partition(':')
        self.assertEqual(result, (L('hello'), L(''), L('')))
    
    def test_partition_multiple_separators(self):
        """Partition uses first occurrence of separator."""
        result = L('a:b:c').partition(':')
        self.assertEqual(result, (L('a'), L(':'), L('b:c')))
    
    def test_partition_multichar_separator(self):
        """Partition with multi-character separator."""
        result = L('hello::world').partition('::')
        self.assertEqual(result, (L('hello'), L('::'), L('world')))
    
    def test_partition_separator_at_start(self):
        """Partition with separator at the start."""
        result = L(':hello').partition(':')
        self.assertEqual(result, (L(''), L(':'), L('hello')))
    
    def test_partition_separator_at_end(self):
        """Partition with separator at the end."""
        result = L('hello:').partition(':')
        self.assertEqual(result, (L('hello'), L(':'), L('')))
    
    def test_partition_empty_string(self):
        """Partition on empty string."""
        result = L('').partition(':')
        self.assertEqual(result, (L(''), L(''), L('')))
    
    def test_partition_empty_separator_raises(self):
        """Partition with empty separator raises ValueError."""
        with self.assertRaises(ValueError):
            L('hello').partition('')
    
    def test_partition_with_L_separator(self):
        """Partition with L instance as separator."""
        result = L('hello:world').partition(L(':'))
        self.assertEqual(result, (L('hello'), L(':'), L('world')))
    
    def test_partition_type_error(self):
        """Partition with invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            L('hello').partition(123)
    
    def test_partition_comparison_with_str(self):
        """Compare L.partition() with str.partition()."""
        test_strings = [
            'hello:world',
            'a:b:c:d',
            'no separator',
            ':start',
            'end:',
            ':::',
            '',
        ]
        for s in test_strings:
            with self.subTest(s=s):
                l_result = L(s).partition(':')
                str_result = s.partition(':')
                expected = tuple(L(part) for part in str_result)
                self.assertEqual(l_result, expected)


class TestRPartition(unittest.TestCase):
    """Test L.rpartition() method"""
    
    def test_rpartition_basic(self):
        """Basic rpartition with separator found."""
        result = L('hello:world').rpartition(':')
        self.assertEqual(result, (L('hello'), L(':'), L('world')))
    
    def test_rpartition_separator_not_found(self):
        """RPartition when separator is not found."""
        result = L('hello').rpartition(':')
        self.assertEqual(result, (L(''), L(''), L('hello')))
    
    def test_rpartition_multiple_separators(self):
        """RPartition uses last occurrence of separator."""
        result = L('a:b:c').rpartition(':')
        self.assertEqual(result, (L('a:b'), L(':'), L('c')))
    
    def test_rpartition_multichar_separator(self):
        """RPartition with multi-character separator."""
        result = L('hello::world').rpartition('::')
        self.assertEqual(result, (L('hello'), L('::'), L('world')))
    
    def test_rpartition_separator_at_start(self):
        """RPartition with separator at the start."""
        result = L(':hello').rpartition(':')
        self.assertEqual(result, (L(''), L(':'), L('hello')))
    
    def test_rpartition_separator_at_end(self):
        """RPartition with separator at the end."""
        result = L('hello:').rpartition(':')
        self.assertEqual(result, (L('hello'), L(':'), L('')))
    
    def test_rpartition_empty_string(self):
        """RPartition on empty string."""
        result = L('').rpartition(':')
        self.assertEqual(result, (L(''), L(''), L('')))
    
    def test_rpartition_empty_separator_raises(self):
        """RPartition with empty separator raises ValueError."""
        with self.assertRaises(ValueError):
            L('hello').rpartition('')
    
    def test_rpartition_with_L_separator(self):
        """RPartition with L instance as separator."""
        result = L('hello:world').rpartition(L(':'))
        self.assertEqual(result, (L('hello'), L(':'), L('world')))
    
    def test_rpartition_type_error(self):
        """RPartition with invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            L('hello').rpartition(123)
    
    def test_rpartition_comparison_with_str(self):
        """Compare L.rpartition() with str.rpartition()."""
        test_strings = [
            'hello:world',
            'a:b:c:d',
            'no separator',
            ':start',
            'end:',
            ':::',
            '',
        ]
        for s in test_strings:
            with self.subTest(s=s):
                l_result = L(s).rpartition(':')
                str_result = s.rpartition(':')
                expected = tuple(L(part) for part in str_result)
                self.assertEqual(l_result, expected)


class TestPartitionVsRPartition(unittest.TestCase):
    """Test differences between partition and rpartition"""
    
    def test_partition_vs_rpartition_single_separator(self):
        """partition and rpartition give same results with single separator."""
        s = L('hello:world')
        self.assertEqual(s.partition(':'), s.rpartition(':'))
    
    def test_partition_vs_rpartition_multiple_separators(self):
        """partition and rpartition differ with multiple separators."""
        s = L('a:b:c')
        part = s.partition(':')
        rpart = s.rpartition(':')
        self.assertEqual(part, (L('a'), L(':'), L('b:c')))
        self.assertEqual(rpart, (L('a:b'), L(':'), L('c')))
    
    def test_partition_vs_rpartition_not_found(self):
        """partition and rpartition differ when separator not found."""
        s = L('hello')
        part = s.partition(':')
        rpart = s.rpartition(':')
        self.assertEqual(part, (L('hello'), L(''), L('')))
        self.assertEqual(rpart, (L(''), L(''), L('hello')))


if __name__ == '__main__':
    unittest.main()
