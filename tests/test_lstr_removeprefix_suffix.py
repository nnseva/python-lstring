#!/usr/bin/env python3
"""
Tests for L.removeprefix() and L.removesuffix() methods.
"""

import unittest
from lstring import L
import lstring


class TestLStrRemoveprefix(unittest.TestCase):
    """Tests for L.removeprefix() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_removeprefix_basic(self):
        """Remove simple prefix."""
        self.assertEqual(L('TestHook').removeprefix('Test'), L('Hook'))
        self.assertEqual(L('hello world').removeprefix('hello '), L('world'))
        self.assertEqual(L('prefix_text').removeprefix('prefix_'), L('text'))
    
    def test_removeprefix_no_match(self):
        """Prefix not found - return unchanged."""
        self.assertEqual(L('BaseTestCase').removeprefix('Test'), L('BaseTestCase'))
        self.assertEqual(L('hello').removeprefix('world'), L('hello'))
        self.assertEqual(L('text').removeprefix('prefix'), L('text'))
    
    def test_removeprefix_empty_prefix(self):
        """Empty prefix returns original string."""
        self.assertEqual(L('hello').removeprefix(''), L('hello'))
        self.assertEqual(L('').removeprefix(''), L(''))
    
    def test_removeprefix_empty_string(self):
        """Empty string with non-empty prefix."""
        self.assertEqual(L('').removeprefix('prefix'), L(''))
    
    def test_removeprefix_full_match(self):
        """Prefix equals entire string."""
        self.assertEqual(L('test').removeprefix('test'), L(''))
        self.assertEqual(L('hello').removeprefix('hello'), L(''))
    
    def test_removeprefix_partial_match(self):
        """Partial match at start."""
        self.assertEqual(L('testing').removeprefix('test'), L('ing'))
        self.assertEqual(L('hello world').removeprefix('hel'), L('lo world'))
    
    def test_removeprefix_case_sensitive(self):
        """Prefix removal is case-sensitive."""
        self.assertEqual(L('Hello').removeprefix('hello'), L('Hello'))
        self.assertEqual(L('HELLO').removeprefix('hello'), L('HELLO'))
        self.assertEqual(L('hello').removeprefix('HELLO'), L('hello'))
    
    def test_removeprefix_with_L_instance(self):
        """Prefix as L instance."""
        self.assertEqual(L('TestHook').removeprefix(L('Test')), L('Hook'))
        self.assertEqual(L('hello').removeprefix(L('hel')), L('lo'))
    
    def test_removeprefix_unicode(self):
        """Unicode prefix removal."""
        self.assertEqual(L('привет мир').removeprefix('привет '), L('мир'))
        self.assertEqual(L('你好世界').removeprefix('你好'), L('世界'))
        self.assertEqual(L('Café').removeprefix('Caf'), L('é'))
    
    def test_removeprefix_lazy_string(self):
        """Test with lazy string (from operations)."""
        # Concatenation
        s = L('pre') + L('fix_text')
        self.assertEqual(s.removeprefix('prefix_'), L('text'))
        
        # Multiplication
        s = L('abc') * 3
        self.assertEqual(s.removeprefix('abc'), L('abcabc'))
        
        # Slice
        s = L('prefix_value')[0:12]
        self.assertEqual(s.removeprefix('prefix_'), L('value'))
    
    def test_removeprefix_consistency_with_python(self):
        """Ensure L.removeprefix() matches str.removeprefix() for various inputs."""
        test_cases = [
            ('TestHook', 'Test'),
            ('BaseTestCase', 'Test'),
            ('hello', ''),
            ('', 'prefix'),
            ('test', 'test'),
            ('testing', 'test'),
            ('Hello', 'hello'),
            ('abc', 'xyz'),
        ]
        
        for string, prefix in test_cases:
            with self.subTest(string=string, prefix=prefix):
                self.assertEqual(
                    str(L(string).removeprefix(prefix)),
                    string.removeprefix(prefix),
                    f"Mismatch for removeprefix({repr(string)}, {repr(prefix)})"
                )


class TestLStrRemovesuffix(unittest.TestCase):
    """Tests for L.removesuffix() method."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_removesuffix_basic(self):
        """Remove simple suffix."""
        self.assertEqual(L('MiscTests').removesuffix('Tests'), L('Misc'))
        self.assertEqual(L('hello world').removesuffix(' world'), L('hello'))
        self.assertEqual(L('text_suffix').removesuffix('_suffix'), L('text'))
    
    def test_removesuffix_no_match(self):
        """Suffix not found - return unchanged."""
        self.assertEqual(L('TmpDirMixin').removesuffix('Tests'), L('TmpDirMixin'))
        self.assertEqual(L('hello').removesuffix('world'), L('hello'))
        self.assertEqual(L('text').removesuffix('suffix'), L('text'))
    
    def test_removesuffix_empty_suffix(self):
        """Empty suffix returns original string."""
        self.assertEqual(L('hello').removesuffix(''), L('hello'))
        self.assertEqual(L('').removesuffix(''), L(''))
    
    def test_removesuffix_empty_string(self):
        """Empty string with non-empty suffix."""
        self.assertEqual(L('').removesuffix('suffix'), L(''))
    
    def test_removesuffix_full_match(self):
        """Suffix equals entire string."""
        self.assertEqual(L('test').removesuffix('test'), L(''))
        self.assertEqual(L('hello').removesuffix('hello'), L(''))
    
    def test_removesuffix_partial_match(self):
        """Partial match at end."""
        self.assertEqual(L('testing').removesuffix('ing'), L('test'))
        self.assertEqual(L('hello world').removesuffix('rld'), L('hello wo'))
    
    def test_removesuffix_case_sensitive(self):
        """Suffix removal is case-sensitive."""
        self.assertEqual(L('Hello').removesuffix('hello'), L('Hello'))
        self.assertEqual(L('HELLO').removesuffix('hello'), L('HELLO'))
        self.assertEqual(L('hello').removesuffix('HELLO'), L('hello'))
    
    def test_removesuffix_with_L_instance(self):
        """Suffix as L instance."""
        self.assertEqual(L('MiscTests').removesuffix(L('Tests')), L('Misc'))
        self.assertEqual(L('hello').removesuffix(L('lo')), L('hel'))
    
    def test_removesuffix_unicode(self):
        """Unicode suffix removal."""
        self.assertEqual(L('привет мир').removesuffix(' мир'), L('привет'))
        self.assertEqual(L('你好世界').removesuffix('世界'), L('你好'))
        self.assertEqual(L('Café').removesuffix('é'), L('Caf'))
    
    def test_removesuffix_lazy_string(self):
        """Test with lazy string (from operations)."""
        # Concatenation
        s = L('text_') + L('suffix')
        self.assertEqual(s.removesuffix('_suffix'), L('text'))
        
        # Multiplication
        s = L('abc') * 3
        self.assertEqual(s.removesuffix('abc'), L('abcabc'))
        
        # Slice
        s = L('value_suffix')[0:12]
        self.assertEqual(s.removesuffix('_suffix'), L('value'))
    
    def test_removesuffix_consistency_with_python(self):
        """Ensure L.removesuffix() matches str.removesuffix() for various inputs."""
        test_cases = [
            ('MiscTests', 'Tests'),
            ('TmpDirMixin', 'Tests'),
            ('hello', ''),
            ('', 'suffix'),
            ('test', 'test'),
            ('testing', 'ing'),
            ('Hello', 'hello'),
            ('abc', 'xyz'),
        ]
        
        for string, suffix in test_cases:
            with self.subTest(string=string, suffix=suffix):
                self.assertEqual(
                    str(L(string).removesuffix(suffix)),
                    string.removesuffix(suffix),
                    f"Mismatch for removesuffix({repr(string)}, {repr(suffix)})"
                )


class TestLStrRemovePrefixSuffixCombined(unittest.TestCase):
    """Combined tests for removeprefix() and removesuffix()."""
    
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)
    
    def test_remove_both_prefix_and_suffix(self):
        """Chain removeprefix() and removesuffix()."""
        s = L('_test_value_')
        result = s.removeprefix('_').removesuffix('_')
        self.assertEqual(result, L('test_value'))
        
        s = L('prefixMIDDLEsuffix')
        result = s.removeprefix('prefix').removesuffix('suffix')
        self.assertEqual(result, L('MIDDLE'))
    
    def test_remove_order_matters(self):
        """Order of operations affects result."""
        s = L('testtest')
        # Remove prefix first
        result1 = s.removeprefix('test').removesuffix('test')
        self.assertEqual(result1, L(''))
        
        # Remove suffix first
        result2 = s.removesuffix('test').removeprefix('test')
        self.assertEqual(result2, L(''))
    
    def test_remove_overlapping(self):
        """Prefix and suffix overlap in middle."""
        s = L('abcabc')
        result = s.removeprefix('abc').removesuffix('abc')
        self.assertEqual(result, L(''))
        
        s = L('testtest')
        result = s.removeprefix('te').removesuffix('st')
        self.assertEqual(result, L('stte'))


if __name__ == '__main__':
    unittest.main()
