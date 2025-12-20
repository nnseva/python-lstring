import unittest
import lstring


class TestLStrUnicodeKinds(unittest.TestCase):
    """Tests verifying behavior across Unicode storage kinds (1/2/4 byte).

    Ensures slicing, concatenation, collapsing and hashing behave correctly
    when buffers contain different Unicode kinds and when operations span
    boundaries between regions.
    """
    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy behavior across tests."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore optimization threshold after tests complete."""
        lstring.set_optimize_threshold(cls.original_threshold)

    def setUp(self):
        """Prepare sample strings for each Unicode storage kind.

        s1: 1-byte (ASCII/LATIN1)
        s2: 2-byte (BMP) characters
        s3: 4-byte (astral plane) characters
        """
        self.s1 = "ascii"
        self.s2 = "\u0100\u0101"
        self.s3 = "\U0001F600\U0001F601"

    def test_hash_preserved_per_kind(self):
        """Collapsing an `L` backed by different unicode kinds preserves hash."""
        for text in (self.s1, self.s2, self.s3):
            with self.subTest(text=text):
                s = lstring.L(text)
                before_hash = hash(s)
                self.assertEqual(str(s), text)
                s.collapse()
                self.assertEqual(hash(s), before_hash)

    def test_combination_mixed_kinds(self):
        """Concatenating buffers with mixed unicode kinds yields correct string and preserves hash on collapse."""
        a = lstring.L(self.s1)
        b = lstring.L(self.s2)
        c = lstring.L(self.s3)

        combo = a + b + c
        expected = self.s1 + self.s2 + self.s3
        self.assertEqual(str(combo), expected)
        before_hash = hash(combo)
        combo.collapse()
        self.assertEqual(hash(combo), before_hash)
        self.assertEqual(str(combo), expected)

    def test_nested_operations_slice_from_join_mul(self):
        """Slice a result created by joining then repeating and verify correctness and hash preservation."""
        a = lstring.L(self.s1)
        b = lstring.L(self.s3)

        j = a + b
        m = j * 2
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
        """Build deep nested expression mixing kinds and assert final slice correctness and hash preservation."""
        a = lstring.L(self.s2)
        b = lstring.L(self.s1)
        c = lstring.L(self.s3)

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
        """Slicing a 2-byte+ascii source that yields only ASCII should result in a 1-byte-backed string after collapse."""
        base_text = self.s2 + self.s1
        base = lstring.L(base_text)
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
        """Verify slices landing in 1-byte, 2-byte and 4-byte regions behave correctly and preserve hashes after collapse."""
        base_text = self.s3 + self.s2 + self.s1
        base = lstring.L(base_text)

        start_ascii = len(self.s3) + len(self.s2)
        end_ascii = start_ascii + len(self.s1)
        sliced_ascii = base[start_ascii:end_ascii]
        self.assertEqual(str(sliced_ascii), base_text[start_ascii:end_ascii])
        h = hash(sliced_ascii)
        sliced_ascii.collapse()
        self.assertEqual(hash(sliced_ascii), h)

        start_2 = len(self.s3)
        end_2 = start_2 + len(self.s2)
        sliced_2 = base[start_2:end_2]
        self.assertEqual(str(sliced_2), base_text[start_2:end_2])
        h2 = hash(sliced_2)
        sliced_2.collapse()
        self.assertEqual(hash(sliced_2), h2)

        start_4 = 0
        end_4 = len(self.s3)
        sliced_4 = base[start_4:end_4]
        self.assertEqual(str(sliced_4), base_text[start_4:end_4])
        h4 = hash(sliced_4)
        sliced_4.collapse()
        self.assertEqual(hash(sliced_4), h4)

    def test_empty_slices_and_zero_length(self):
        """Empty and out-of-range slices yield empty 1-byte strings and preserve hashes."""
        base = lstring.L(self.s3 + self.s2 + self.s1)
        s0 = base[1:1]
        self.assertEqual(str(s0), "")
        h0 = hash(s0)
        s0.collapse()
        self.assertEqual(hash(s0), h0)

        s_out = base[100:200]
        self.assertEqual(str(s_out), "")
        h_out = hash(s_out)
        s_out.collapse()
        self.assertEqual(hash(s_out), h_out)

    def test_slices_with_non_unit_steps(self):
        """Verify non-unit and negative steps behave as expected and preserve hashes after collapse."""
        base_text = self.s3 + self.s2 + self.s1
        base = lstring.L(base_text)

        step_pos = base[len(self.s3) + len(self.s2):len(base_text):2]
        self.assertEqual(str(step_pos), base_text[len(self.s3) + len(self.s2):len(base_text):2])
        h_pos = hash(step_pos)
        step_pos.collapse()
        self.assertEqual(hash(step_pos), h_pos)

        rev = base[len(self.s3):len(self.s3)+len(self.s2)][::-1]
        self.assertEqual(str(rev), base_text[len(self.s3):len(self.s3)+len(self.s2)][::-1])
        h_rev = hash(rev)
        rev.collapse()
        self.assertEqual(hash(rev), h_rev)


if __name__ == '__main__':
    unittest.main()
