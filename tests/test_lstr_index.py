"""
Tests for index() and rindex() methods.
"""
import unittest
from lstring import L
import lstring


class TestIndex(unittest.TestCase):
    """Tests for index() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_basic_index(self):
        """Basic index with substring found."""
        self.assertEqual(L("hello world").index("world"), 6)
        self.assertEqual(L("hello world").index("hello"), 0)
        self.assertEqual(L("hello world").index("o"), 4)
    
    def test_index_not_found(self):
        """Index raises ValueError when substring not found."""
        with self.assertRaises(ValueError) as cm:
            L("hello world").index("goodbye")
        self.assertEqual(str(cm.exception), "substring not found")
    
    def test_index_empty_substring(self):
        """Index with empty substring."""
        self.assertEqual(L("hello").index(""), 0)
        self.assertEqual(L("").index(""), 0)
    
    def test_index_with_start(self):
        """Index with start parameter."""
        s = L("hello hello")
        self.assertEqual(s.index("hello"), 0)
        self.assertEqual(s.index("hello", 1), 6)
        self.assertEqual(s.index("lo", 4), 9)
        
        # Not found after start
        with self.assertRaises(ValueError):
            s.index("hello", 7)
    
    def test_index_with_start_and_end(self):
        """Index with both start and end parameters."""
        s = L("hello world hello")
        self.assertEqual(s.index("world", 0, 11), 6)
        self.assertEqual(s.index("hello", 0, 5), 0)
        
        # Not found in range
        with self.assertRaises(ValueError):
            s.index("hello", 1, 5)
    
    def test_index_with_L_instance(self):
        """Index with L instance as substring."""
        self.assertEqual(L("hello world").index(L("world")), 6)
    
    def test_comparison_with_str(self):
        """Compare behavior with Python str."""
        test_cases = [
            ("hello world", "world", None, None),
            ("hello world", "hello", None, None),
            ("hello hello", "hello", 1, None),
            ("hello world hello", "world", 0, 11),
            ("test", "", 0, None),
        ]
        for s, sub, start, end in test_cases:
            ls = L(s)
            if start is None and end is None:
                self.assertEqual(ls.index(sub), s.index(sub),
                               f"Failed for index({repr(sub)})")
            elif end is None:
                self.assertEqual(ls.index(sub, start), s.index(sub, start),
                               f"Failed for index({repr(sub)}, {start})")
            else:
                self.assertEqual(ls.index(sub, start, end), s.index(sub, start, end),
                               f"Failed for index({repr(sub)}, {start}, {end})")
    
    def test_valueerror_comparison_with_str(self):
        """ValueError matches str behavior."""
        test_cases = [
            ("hello", "goodbye"),
            ("hello world", "hello", 1, 5),
            ("test", "x", 10),
        ]
        for test_case in test_cases:
            s = test_case[0]
            args = test_case[1:]
            ls = L(s)
            
            # Both should raise ValueError
            with self.assertRaises(ValueError):
                ls.index(*args)
            with self.assertRaises(ValueError):
                s.index(*args)


class TestRIndex(unittest.TestCase):
    """Tests for rindex() method."""
    
    def test_basic_rindex(self):
        """Basic rindex with substring found."""
        self.assertEqual(L("hello world").rindex("world"), 6)
        self.assertEqual(L("hello world").rindex("hello"), 0)
        self.assertEqual(L("hello world").rindex("o"), 7)  # Last 'o'
    
    def test_rindex_not_found(self):
        """Rindex raises ValueError when substring not found."""
        with self.assertRaises(ValueError) as cm:
            L("hello world").rindex("goodbye")
        self.assertEqual(str(cm.exception), "substring not found")
    
    def test_rindex_empty_substring(self):
        """Rindex with empty substring."""
        self.assertEqual(L("hello").rindex(""), 5)  # End of string
        self.assertEqual(L("").rindex(""), 0)
    
    def test_rindex_multiple_occurrences(self):
        """Rindex finds last occurrence."""
        s = L("hello hello hello")
        self.assertEqual(s.rindex("hello"), 12)
        self.assertEqual(s.rindex("lo"), 15)
    
    def test_rindex_with_start(self):
        """Rindex with start parameter."""
        s = L("hello hello")
        self.assertEqual(s.rindex("hello"), 6)
        self.assertEqual(s.rindex("hello", 6), 6)
        self.assertEqual(s.rindex("llo", 3), 8)
        
        # Not found in range starting from start
        with self.assertRaises(ValueError):
            s.rindex("hello", 7)
    
    def test_rindex_with_start_and_end(self):
        """Rindex with both start and end parameters."""
        s = L("hello world hello")
        self.assertEqual(s.rindex("hello", 0, 5), 0)
        self.assertEqual(s.rindex("o", 0, 8), 7)
        
        # Not found in range
        with self.assertRaises(ValueError):
            s.rindex("hello", 6, 11)
    
    def test_rindex_with_L_instance(self):
        """Rindex with L instance as substring."""
        self.assertEqual(L("hello world hello").rindex(L("hello")), 12)
    
    def test_comparison_with_str(self):
        """Compare behavior with Python str."""
        test_cases = [
            ("hello world", "world", None, None),
            ("hello world", "o", None, None),  # Last 'o'
            ("hello hello", "hello", None, None),
            ("hello world hello", "hello", 0, 17),
            ("test", "", None, None),
        ]
        for s, sub, start, end in test_cases:
            ls = L(s)
            if start is None and end is None:
                self.assertEqual(ls.rindex(sub), s.rindex(sub),
                               f"Failed for rindex({repr(sub)})")
            elif end is None:
                self.assertEqual(ls.rindex(sub, start), s.rindex(sub, start),
                               f"Failed for rindex({repr(sub)}, {start})")
            else:
                self.assertEqual(ls.rindex(sub, start, end), s.rindex(sub, start, end),
                               f"Failed for rindex({repr(sub)}, {start}, {end})")
    
    def test_valueerror_comparison_with_str(self):
        """ValueError matches str behavior."""
        test_cases = [
            ("hello", "goodbye"),
            ("hello world hello", "world", 11, 17),
            ("test", "x", 0, 0),
        ]
        for test_case in test_cases:
            s = test_case[0]
            args = test_case[1:]
            ls = L(s)
            
            # Both should raise ValueError
            with self.assertRaises(ValueError):
                ls.rindex(*args)
            with self.assertRaises(ValueError):
                s.rindex(*args)


class TestIndexRindexBufferTypes(unittest.TestCase):
    """Test index/rindex work correctly with different buffer types."""
    
    def test_slice_buffer(self):
        """Test with SliceBuffer."""
        s = L("xxxhello worldxxx")[3:-3]
        self.assertEqual(s.index("world"), 6)
        self.assertEqual(s.rindex("hello"), 0)
        
        with self.assertRaises(ValueError):
            s.index("xxx")
    
    def test_join_buffer(self):
        """Test with JoinBuffer."""
        s = L("hello") + L(" ") + L("world")
        self.assertEqual(s.index("world"), 6)
        self.assertEqual(s.rindex("hello"), 0)
        self.assertEqual(s.index(" "), 5)
    
    def test_mul_buffer(self):
        """Test with MulBuffer."""
        s = L("abc") * 3
        self.assertEqual(s.index("abc"), 0)
        self.assertEqual(s.rindex("abc"), 6)
        self.assertEqual(s.index("ca"), 2)
        self.assertEqual(s.rindex("ca"), 5)


class TestIndexVsFind(unittest.TestCase):
    """Test that index and find return same values (except when not found)."""
    
    def test_index_equals_find_when_found(self):
        """Index should return same value as find when substring is found."""
        test_cases = [
            L("hello world"),
            L("abc") * 5,
            L("test") + L(" ") + L("string"),
            L("abcdefg")[1:-1],
        ]
        search_strings = ["a", "e", "test", ""]
        
        for s in test_cases:
            for search in search_strings:
                find_result = s.find(search)
                if find_result != -1:
                    self.assertEqual(s.index(search), find_result)
                else:
                    with self.assertRaises(ValueError):
                        s.index(search)
    
    def test_rindex_equals_rfind_when_found(self):
        """Rindex should return same value as rfind when substring is found."""
        test_cases = [
            L("hello world"),
            L("abc") * 5,
            L("test") + L(" ") + L("string"),
            L("abcdefg")[1:-1],
        ]
        search_strings = ["a", "e", "test", ""]
        
        for s in test_cases:
            for search in search_strings:
                rfind_result = s.rfind(search)
                if rfind_result != -1:
                    self.assertEqual(s.rindex(search), rfind_result)
                else:
                    with self.assertRaises(ValueError):
                        s.rindex(search)


if __name__ == '__main__':
    unittest.main()
