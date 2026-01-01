"""Reference-counting tests for lstring.re Pattern and Match objects.

These tests verify that Pattern and Match objects do not leak references
or hold unnecessary references to their source objects.
"""

import unittest
import sys
import gc
import lstring
import lstring.re
from lstring import L


def dyn(s: str) -> str:
    """Create a dynamic (non-interned) string equal to `s`.
    
    Using join creates a new string object at runtime and avoids interned
    literal behavior.
    """
    r = "".join(s)
    if sys.getrefcount(r) > 2:
        raise RuntimeError("Failed to create dynamic string")
    return r


class TestPatternRefCounts(unittest.TestCase):
    """Reference-counting tests for Pattern objects."""

    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy buffer behavior."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore the optimization threshold after the test class finishes."""
        lstring.set_optimize_threshold(cls.original_threshold)
    
    def setUp(self):
        """Collect garbage before each test to stabilize reference counts."""
        gc.collect()
    
    def tearDown(self):
        """Collect garbage after each test to clean up temporary objects."""
        gc.collect()
    
    def test_pattern_creation_from_str(self):
        """Creating Pattern from str does not leak references."""
        pattern_str = dyn(r'\w+')
        before = sys.getrefcount(pattern_str)
        
        pattern = lstring.re.compile(pattern_str, compatible=False)
        del pattern
        gc.collect()
        
        after = sys.getrefcount(pattern_str)
        self.assertEqual(after, before)
    
    def test_pattern_creation_from_L(self):
        """Creating Pattern from L does not leak references."""
        pattern_str = dyn(r'\d+')
        pattern_L = L(pattern_str)
        
        before_str = sys.getrefcount(pattern_str)
        before_L = sys.getrefcount(pattern_L)
        
        pattern = lstring.re.compile(pattern_L, compatible=False)
        del pattern
        gc.collect()
        
        after_str = sys.getrefcount(pattern_str)
        after_L = sys.getrefcount(pattern_L)
        
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_L, before_L)
    
    def test_pattern_multiple_uses(self):
        """Using Pattern multiple times does not accumulate references."""
        pattern_str = dyn(r'\w+')
        test_str = dyn('test')
        test_L = L(test_str)
        
        pattern = lstring.re.compile(pattern_str, compatible=False)
        
        before_pattern = sys.getrefcount(pattern)
        before_str = sys.getrefcount(test_str)
        before_L = sys.getrefcount(test_L)
        
        # Multiple operations
        result = pattern.match(test_L)
        del result
        result = pattern.search(test_L)
        del result
        result = pattern.findall(test_L)
        del result
        
        after_pattern = sys.getrefcount(pattern)
        after_str = sys.getrefcount(test_str)
        after_L = sys.getrefcount(test_L)
        
        self.assertEqual(after_pattern, before_pattern)
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_L, before_L)
    
    def test_pattern_with_compatible_conversion(self):
        """Pattern with compatible=True does not leak references."""
        pattern_str = dyn(r'(?P<name>\w+)')
        before = sys.getrefcount(pattern_str)
        
        pattern = lstring.re.compile(pattern_str, compatible=True)
        del pattern
        gc.collect()
        
        after = sys.getrefcount(pattern_str)
        self.assertEqual(after, before)


class TestMatchRefCounts(unittest.TestCase):
    """Reference-counting tests for Match objects."""

    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy buffer behavior."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore the optimization threshold after the test class finishes."""
        lstring.set_optimize_threshold(cls.original_threshold)
    
    def setUp(self):
        """Collect garbage before each test to stabilize reference counts."""
        gc.collect()
    
    def tearDown(self):
        """Collect garbage after each test to clean up temporary objects."""
        gc.collect()
    
    def test_match_creation(self):
        """Creating and deleting Match does not leak references."""
        subject_str = dyn('test123')
        subject = L(subject_str)
        pattern = lstring.re.compile(r'\w+', compatible=False)
        
        before_str = sys.getrefcount(subject_str)
        before_subject = sys.getrefcount(subject)
        before_pattern = sys.getrefcount(pattern)
        
        match = pattern.match(subject)
        del match
        gc.collect()
        
        after_str = sys.getrefcount(subject_str)
        after_subject = sys.getrefcount(subject)
        after_pattern = sys.getrefcount(pattern)
        
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_subject, before_subject)
        self.assertEqual(after_pattern, before_pattern)
    
    def test_match_group_access(self):
        """Accessing match groups does not leak references."""
        subject_str = dyn('test123')
        subject = L(subject_str)
        pattern = lstring.re.compile(r'(\w+)(\d+)', compatible=False)
        match = pattern.match(subject)
        
        before_str = sys.getrefcount(subject_str)
        before_match = sys.getrefcount(match)
        
        # Multiple group accesses
        result = match.group(0)
        del result
        result = match.group(1)
        del result
        result = match.group(2)
        del result
        result = match.groups()
        del result
        
        after_str = sys.getrefcount(subject_str)
        after_match = sys.getrefcount(match)
        
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_match, before_match)
    
    def test_match_with_named_groups(self):
        """Match with named groups does not leak references."""
        subject_str = dyn('test123')
        subject = L(subject_str)
        pattern = lstring.re.compile(r'(?<word>\w+)(?<num>\d+)', compatible=False)
        
        before_str = sys.getrefcount(subject_str)
        before_subject = sys.getrefcount(subject)
        
        match = pattern.match(subject)
        result = match.group(L('word'))
        del result
        result = match.group(L('num'))
        del result
        del match
        gc.collect()
        
        after_str = sys.getrefcount(subject_str)
        after_subject = sys.getrefcount(subject)
        
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_subject, before_subject)
    
    def test_match_span_operations(self):
        """Match span/start/end operations do not leak references."""
        subject_str = dyn('test')
        subject = L(subject_str)
        pattern = lstring.re.compile(r'\w+', compatible=False)
        match = pattern.match(subject)
        
        before_str = sys.getrefcount(subject_str)
        before_match = sys.getrefcount(match)
        
        result = match.start()
        del result
        result = match.end()
        del result
        result = match.span()
        del result
        
        after_str = sys.getrefcount(subject_str)
        after_match = sys.getrefcount(match)
        
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_match, before_match)
    
    def test_match_expand(self):
        """Match.expand() does not leak references."""
        subject_str = dyn('test')
        subject = L(subject_str)
        template_str = dyn(r'\1_suffix')
        template = L(template_str)
        
        pattern = lstring.re.compile(r'(\w+)', compatible=False)
        match = pattern.match(subject)
        
        before_subject_str = sys.getrefcount(subject_str)
        before_template_str = sys.getrefcount(template_str)
        before_match = sys.getrefcount(match)
        before_template = sys.getrefcount(template)
        
        result = match.expand(template)
        del result
        gc.collect()
        
        after_subject_str = sys.getrefcount(subject_str)
        after_template_str = sys.getrefcount(template_str)
        after_match = sys.getrefcount(match)
        after_template = sys.getrefcount(template)
        
        self.assertEqual(after_subject_str, before_subject_str)
        self.assertEqual(after_template_str, before_template_str)
        self.assertEqual(after_match, before_match)
        self.assertEqual(after_template, before_template)


class TestPatternMatchInteraction(unittest.TestCase):
    """Reference-counting tests for Pattern-Match interactions."""
    
    def setUp(self):
        """Collect garbage before each test to stabilize reference counts."""
        gc.collect()
    
    def tearDown(self):
        """Collect garbage after each test to clean up temporary objects."""
        gc.collect()
    
    def test_multiple_matches_from_pattern(self):
        """Creating multiple matches from same pattern does not leak."""
        pattern = lstring.re.compile(r'\w+', compatible=False)
        
        str1 = dyn('test1')
        str2 = dyn('test2')
        str3 = dyn('test3')
        subjects = [L(str1), L(str2), L(str3)]
        
        before_pattern = sys.getrefcount(pattern)
        before_str1 = sys.getrefcount(str1)
        before_str2 = sys.getrefcount(str2)
        before_str3 = sys.getrefcount(str3)
        
        matches = [pattern.match(s) for s in subjects]
        del matches
        gc.collect()
        
        after_pattern = sys.getrefcount(pattern)
        after_str1 = sys.getrefcount(str1)
        after_str2 = sys.getrefcount(str2)
        after_str3 = sys.getrefcount(str3)
        
        self.assertEqual(after_pattern, before_pattern)
        self.assertEqual(after_str1, before_str1)
        self.assertEqual(after_str2, before_str2)
        self.assertEqual(after_str3, before_str3)
    
    def test_finditer_does_not_leak(self):
        """Using finditer does not leak references."""
        subject_str = dyn('test1 test2 test3')
        subject = L(subject_str)
        pattern = lstring.re.compile(r'\w+', compatible=False)
        
        before_str = sys.getrefcount(subject_str)
        before_subject = sys.getrefcount(subject)
        before_pattern = sys.getrefcount(pattern)
        
        matches = list(pattern.finditer(subject))
        del matches
        gc.collect()
        
        after_str = sys.getrefcount(subject_str)
        after_subject = sys.getrefcount(subject)
        after_pattern = sys.getrefcount(pattern)
        
        self.assertEqual(after_str, before_str)
        self.assertEqual(after_subject, before_subject)
        self.assertEqual(after_pattern, before_pattern)
    
    def test_sub_does_not_leak(self):
        """Pattern.sub() does not leak references."""
        subject_str = dyn('test123test456')
        subject = L(subject_str)
        replacement_str = dyn('XXX')
        replacement = L(replacement_str)
        pattern = lstring.re.compile(r'\d+', compatible=False)
        
        before_subject_str = sys.getrefcount(subject_str)
        before_subject = sys.getrefcount(subject)
        before_pattern = sys.getrefcount(pattern)
        before_replacement_str = sys.getrefcount(replacement_str)
        before_replacement = sys.getrefcount(replacement)
        
        result = pattern.sub(replacement, subject)
        del result
        gc.collect()
        
        after_subject_str = sys.getrefcount(subject_str)
        after_subject = sys.getrefcount(subject)
        after_pattern = sys.getrefcount(pattern)
        after_replacement_str = sys.getrefcount(replacement_str)
        after_replacement = sys.getrefcount(replacement)
        
        self.assertEqual(after_subject_str, before_subject_str)
        self.assertEqual(after_subject, before_subject)
        self.assertEqual(after_pattern, before_pattern)
        self.assertEqual(after_replacement_str, before_replacement_str)
        self.assertEqual(after_replacement, before_replacement)


if __name__ == '__main__':
    unittest.main()
