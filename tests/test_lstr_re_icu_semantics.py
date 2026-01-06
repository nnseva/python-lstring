import unittest

import _lstring
import lstring
import lstring.re
from lstring import L


class TestICURegexSemantics(unittest.TestCase):
    def test_ignorecase_cyrillic_fullmatch(self):
        # Cyrillic casing is 1:1, good for ICU u_foldCase(UChar32)
        pat = lstring.re.compile('привет', flags=_lstring.re.IGNORECASE, compatible=False)
        self.assertIsNotNone(pat.fullmatch(L('ПРИВЕТ')))

    def test_ignorecase_greek_sigma_variants(self):
        # Greek sigma has a special final form ς; Unicode casefold maps both σ/ς to σ.
        pat = lstring.re.compile('σ', flags=_lstring.re.IGNORECASE, compatible=False)
        self.assertIsNotNone(pat.search(L('Σ')))
        self.assertIsNotNone(pat.search(L('ς')))

    def test_word_class_matches_cyrillic_and_underscore(self):
        pat = lstring.re.compile(r'^\w+$', compatible=False)
        self.assertIsNotNone(pat.fullmatch(L('привет_123')))

    def test_digit_class_matches_arabic_indic(self):
        # Arabic-Indic digits are General Category Nd and should match \d under Unicode-aware traits.
        pat = lstring.re.compile(r'^\d+$', compatible=False)
        self.assertIsNotNone(pat.fullmatch(L('١٢٣')))

    def test_space_class_matches_em_space(self):
        # U+2003 EM SPACE should be treated as whitespace.
        pat = lstring.re.compile(r'\s', compatible=False)
        self.assertIsNotNone(pat.search(L('a\u2003b')))

    def test_posix_alpha_class_matches_cyrillic(self):
        # POSIX alpha class should include non-ASCII letters under Unicode-aware traits.
        pat = lstring.re.compile(r'^[[:alpha:]]+$', compatible=False)
        self.assertIsNotNone(pat.fullmatch(L('привет')))
