import unittest
import lstring


class TestLStrUnicodeKinds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Ensure tests run with optimization disabled to preserve lazy buffer behavior
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls): 
        # Restore default optimization setting after tests
        lstring.set_optimize_threshold(cls.original_threshold)

    def setUp(self):
        # 1-byte (ASCII/LATIN1 <= 0xFF)
        self.s1 = "ascii"
        # 2-byte (codepoints > 0xFF and <= 0xFFFF)
        self.s2 = "\u0100\u0101"  # U+0100, U+0101
        # 4-byte (codepoints > 0xFFFF)
        self.s3 = "\U0001F600\U0001F601"  # two emoji

    def test_hash_preserved_per_kind(self):
        for text in (self.s1, self.s2, self.s3):
            with self.subTest(text=text):
                s = lstring._lstr(text)
                before_hash = hash(s)
                # sanity
                self.assertEqual(str(s), text)
                # collapse and ensure hash preserved
                s.collapse()
                self.assertEqual(hash(s), before_hash)

    def test_combination_mixed_kinds(self):
        a = lstring._lstr(self.s1)
        b = lstring._lstr(self.s2)
        c = lstring._lstr(self.s3)

        combo = a + b + c
        expected = self.s1 + self.s2 + self.s3
        self.assertEqual(str(combo), expected)
        before_hash = hash(combo)
        combo.collapse()
        self.assertEqual(hash(combo), before_hash)
        self.assertEqual(str(combo), expected)

    def test_nested_operations_slice_from_join_mul(self):
        a = lstring._lstr(self.s1)
        b = lstring._lstr(self.s3)

        # join then mul then slice
        j = a + b
        m = j * 2
        # pick a slice spanning the join boundary
        start = len(self.s1) - 2
        end = start + 6
        s = m[start:end]

        expected = (self.s1 + self.s3) * 2
        expected_slice = expected[start:end]
        self.assertEqual(str(s), expected_slice)
        before_hash = hash(s)
        s.collapse()
        self.assertEqual(hash(s), before_hash)
        self.assertEqual(str(s), expected_slice)

    def test_deeply_nested_mix(self):
        # combine multiple operations of different kinds
        a = lstring._lstr(self.s2)
        b = lstring._lstr(self.s1)
        c = lstring._lstr(self.s3)

        # ((a * 3) + (b + c))[2:10]
        expr = (a * 3) + (b + c)
        sliced = expr[2:10]
        expected = (self.s2 * 3) + (self.s1 + self.s3)
        expected_slice = expected[2:10]

        self.assertEqual(str(sliced), expected_slice)
        before_hash = hash(sliced)
        sliced.collapse()
        self.assertEqual(hash(sliced), before_hash)
        self.assertEqual(str(sliced), expected_slice)

    def test_slice_from_2byte_source_yields_1byte_when_ascii_only(self):
        # source is 2-byte then ascii, slice only the ascii tail
        base_text = self.s2 + self.s1
        base = lstring._lstr(base_text)
        # slice the ascii part
        start = len(self.s2)
        end = start + len(self.s1)
        sliced = base[start:end]
        expected = base_text[start:end]
        self.assertEqual(str(sliced), expected)
        before_hash = hash(sliced)
        sliced.collapse()
        self.assertEqual(hash(sliced), before_hash)
        self.assertEqual(str(sliced), expected)

    def test_slice_from_4byte_source_various_kinds(self):
        # source contains 4-byte, 2-byte and 1-byte segments
        base_text = self.s3 + self.s2 + self.s1
        base = lstring._lstr(base_text)

        # slice that lands entirely in the ascii (1-byte) region
        start_ascii = len(self.s3) + len(self.s2)
        end_ascii = start_ascii + len(self.s1)
        sliced_ascii = base[start_ascii:end_ascii]
        self.assertEqual(str(sliced_ascii), base_text[start_ascii:end_ascii])
        h = hash(sliced_ascii)
        sliced_ascii.collapse()
        self.assertEqual(hash(sliced_ascii), h)

        # slice that lands entirely in the 2-byte region
        start_2 = len(self.s3)
        end_2 = start_2 + len(self.s2)
        sliced_2 = base[start_2:end_2]
        self.assertEqual(str(sliced_2), base_text[start_2:end_2])
        h2 = hash(sliced_2)
        sliced_2.collapse()
        self.assertEqual(hash(sliced_2), h2)

        # slice that lands entirely in the 4-byte region
        start_4 = 0
        end_4 = len(self.s3)
        sliced_4 = base[start_4:end_4]
        self.assertEqual(str(sliced_4), base_text[start_4:end_4])
        h4 = hash(sliced_4)
        sliced_4.collapse()
        self.assertEqual(hash(sliced_4), h4)

    def test_empty_slices_and_zero_length(self):
        # empty slice from any source should be empty and 1-byte by convention
        base = lstring._lstr(self.s3 + self.s2 + self.s1)
        # zero-length slice
        s0 = base[1:1]
        self.assertEqual(str(s0), "")
        h0 = hash(s0)
        s0.collapse()
        self.assertEqual(hash(s0), h0)

        # slice outside range should be empty
        s_out = base[100:200]
        self.assertEqual(str(s_out), "")
        h_out = hash(s_out)
        s_out.collapse()
        self.assertEqual(hash(s_out), h_out)

    def test_slices_with_non_unit_steps(self):
        # construct a mixed-kind base
        base_text = self.s3 + self.s2 + self.s1
        base = lstring._lstr(base_text)

        # positive step >1 that picks only ascii characters (1-byte)
        step_pos = base[len(self.s3) + len(self.s2):len(base_text):2]
        self.assertEqual(str(step_pos), base_text[len(self.s3) + len(self.s2):len(base_text):2])
        h_pos = hash(step_pos)
        step_pos.collapse()
        self.assertEqual(hash(step_pos), h_pos)

        # negative step that reverses a region containing mixed kinds
        rev = base[len(self.s3):len(self.s3)+len(self.s2)][::-1]
        self.assertEqual(str(rev), base_text[len(self.s3):len(self.s3)+len(self.s2)][::-1])
        h_rev = hash(rev)
        rev.collapse()
        self.assertEqual(hash(rev), h_rev)


if __name__ == '__main__':
    unittest.main()
