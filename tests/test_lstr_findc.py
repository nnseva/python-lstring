import sys
import unittest

import lstring
from lstring import L

class TestLStrFindC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic behavior
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)

    def test_strbuffer_kinds(self):
        # ASCII (1-byte), some BMP (>0xFF), and astral (>0xFFFF)
        s1 = 'hello world'
        s2 = 'héllo'  # contains e-acute -> 2-byte in some builds
        s3 = 'a\U0001F600b'  # includes a 4-byte code point (emoji)
        for s in (s1, s2, s3):
            l = L(s)
            for ch in set(s):
                # findc with char and with ord
                expected = s.find(ch)
                self.assertEqual(l.findc(ch), expected)
                self.assertEqual(l.findc(ord(ch)), expected)
                # rfindc
                expected_r = s.rfind(ch)
                self.assertEqual(l.rfindc(ch), expected_r)
                self.assertEqual(l.rfindc(ord(ch)), expected_r)

    def test_joinbuffer_boundaries(self):
        a = 'abcde'
        b = 'XYZ'
        S = L(a) + b
        full = a + b
        # search across join
        self.assertEqual(S.findc('X'), full.find('X'))
        # range covering join: end in left, start in left
        self.assertEqual(S.findc('X', 2, 7), full.find('X', 2, 7))
        # range adjacent to join: search end at join boundary
        self.assertEqual(S.findc('X', 0, len(a)), full.find('X', 0, len(a)))
        # rfindc similarly
        self.assertEqual(S.rfindc('a'), full.rfind('a'))
        self.assertEqual(S.rfindc('a', 0, 3), full.rfind('a', 0, 3))

    def test_mulbuffer_various_spans(self):
        base = 'abC'
        # repeat 5 times
        M = L(base) * 5
        full = base * 5
        # search whole
        for ch in set(full):
            self.assertEqual(M.findc(ch), full.find(ch))
            self.assertEqual(M.rfindc(ch), full.rfind(ch))
        # ranges capturing 1..4 blocks
        length = len(base)
        # 1 block: somewhere inside first block
        self.assertEqual(M.findc('C', 0, length), full.find('C', 0, length))
        # 2 blocks: from mid of block0 to mid of block2
        self.assertEqual(M.findc('b', 1, 2*length+1), full.find('b', 1, 2*length+1))
        # 3 blocks
        self.assertEqual(M.findc('a', 0, 3*length), full.find('a', 0, 3*length))
        # 4 blocks
        self.assertEqual(M.findc('a', 2, 4*length+1), full.find('a', 2, 4*length+1))
        # ranges that border repeats
        self.assertEqual(M.findc('a', length, length+1), full.find('a', length, length+1))
        self.assertEqual(M.rfindc('a', 0, 2*length), full.rfind('a', 0, 2*length))

    def test_slice1buffer(self):
        s = '0123456789'
        S = L(s)[2:8]
        sub = s[2:8]
        for ch in set(sub):
            self.assertEqual(S.findc(ch), sub.find(ch))
            self.assertEqual(S.rfindc(ch), sub.rfind(ch))
        # with range
        self.assertEqual(S.findc('5', 0, 2), sub.find('5', 0, 2))
        self.assertEqual(S.rfindc('5', 0, 2), sub.rfind('5', 0, 2))

    def test_slicebuffer_step(self):
        s = 'abcdefghij'
        # step 2 slice
        S = L(s)[1:9:2]
        sub = s[1:9:2]
        for ch in set(sub):
            self.assertEqual(S.findc(ch), sub.find(ch))
            self.assertEqual(S.rfindc(ch), sub.rfind(ch))
        # with ranges
        self.assertEqual(S.findc(sub[0], 0, 1), sub.find(sub[0], 0, 1))
        self.assertEqual(S.rfindc(sub[-1], 0, len(sub)), sub.rfind(sub[-1], 0, len(sub)))

    def test_unicode_kind_boundary_1byte(self):
        """Test that searching for characters beyond 1-byte kind (>0xFF) returns -1"""
        # ASCII string has 1-byte unicode_kind
        s = L('hello')
        
        # Character U+0141 (Ł) has value 0x141 (321)
        # Its lower byte is 0x41 which is 'A'
        # If we don't check unicode_kind, we might get false match with 'A'
        result = s.findc(0x0141)
        self.assertEqual(result, -1, "Character beyond 1-byte kind should not be found")
        
        result = s.rfindc(0x0141)
        self.assertEqual(result, -1, "Character beyond 1-byte kind should not be found in rfindc")
        
        # Character U+03B1 (α - Greek alpha) has value 0x3B1 (945)
        # Its lower byte is 0xB1
        result = s.findc(0x03B1)
        self.assertEqual(result, -1, "Greek alpha beyond 1-byte kind should not be found")
        
        # Even if the string contains 'A' (0x41), searching for U+0141 should not match
        s_with_a = L('hallo')
        result = s_with_a.findc(0x0141)
        self.assertEqual(result, -1, "U+0141 should not match 'a' despite lower byte collision")

    def test_unicode_kind_boundary_2byte(self):
        """Test that searching for characters beyond 2-byte kind (>0xFFFF) returns -1"""
        # String with Latin Extended character (2-byte kind)
        s = L('héllo')  # 'é' is U+00E9
        
        # Emoji U+1F600 (😀) has value 0x1F600
        # Its lower 2 bytes are 0xF600
        result = s.findc(0x1F600)
        self.assertEqual(result, -1, "Emoji beyond 2-byte kind should not be found")
        
        result = s.rfindc(0x1F600)
        self.assertEqual(result, -1, "Emoji beyond 2-byte kind should not be found in rfindc")
        
        # Character beyond 2-byte range
        result = s.findc(0x10000)
        self.assertEqual(result, -1, "Character U+10000 beyond 2-byte kind should not be found")

    def test_unicode_kind_boundary_valid_searches(self):
        """Test that valid searches within unicode_kind still work correctly"""
        # 1-byte string
        s1 = L('hello')
        self.assertEqual(s1.findc('h'), 0)
        self.assertEqual(s1.findc(ord('h')), 0)
        self.assertEqual(s1.findc(0x68), 0)  # 'h' as int
        
        # 2-byte string
        s2 = L('héllo')
        self.assertEqual(s2.findc('é'), 1)
        self.assertEqual(s2.findc(0x00E9), 1)  # 'é' as int (U+00E9)
        
        # 4-byte string
        s3 = L('a😀b')
        self.assertEqual(s3.findc('😀'), 1)
        self.assertEqual(s3.findc(0x1F600), 1)  # emoji as int

    def test_unicode_kind_edge_cases(self):
        """Test edge cases at unicode_kind boundaries"""
        # Test maximum valid value for 1-byte kind
        s1 = L('test')
        self.assertEqual(s1.findc(0xFF), -1)  # 0xFF is valid for 1-byte but not in 'test'
        
        # Test boundary: 0xFF is last valid 1-byte, 0x100 is first invalid
        self.assertEqual(s1.findc(0x100), -1)
        
        # Test maximum valid value for 2-byte kind
        s2 = L('tëst')  # forces 2-byte
        self.assertEqual(s2.findc(0xFFFF), -1)  # valid for 2-byte but not in string
        self.assertEqual(s2.findc(0x10000), -1)  # first invalid for 2-byte

    def test_unicode_kind_boundary_with_concat(self):
        """Test that concatenation preserves correct unicode_kind handling"""
        # 1-byte + 1-byte
        s1 = L('hello')
        s2 = L('world')
        result = (s1 + s2).findc(0x0141)  # U+0141 (Ł) beyond 1-byte
        self.assertEqual(result, -1, "Concatenated 1-byte strings should not find U+0141")
        
        # 1-byte + 2-byte
        s3 = L('hello')
        s4 = L('wörld')  # 'ö' is 2-byte
        concat = s3 + s4
        result = concat.findc(0x1F600)  # Emoji beyond 2-byte
        self.assertEqual(result, -1, "Concatenated 1+2-byte strings should not find emoji")
        
        # Verify valid search still works
        result = concat.findc('ö')
        self.assertGreater(result, 0, "Should find 'ö' in concatenated string")
        
        # Mixed concat with potential lower-byte collision
        s5 = L('hallo')  # contains 'a' (0x41)
        s6 = L('test')
        result = (s5 + s6).findc(0x0141)  # Should not match 'a'
        self.assertEqual(result, -1, "U+0141 should not match 'a' in concatenation")

    def test_unicode_kind_boundary_with_slices(self):
        """Test that slicing preserves correct unicode_kind handling"""
        # Slice from 1-byte string
        s1 = L('hello world')
        slice_result = s1[2:8]
        result = slice_result.findc(0x0141)  # U+0141 beyond 1-byte
        self.assertEqual(result, -1, "Sliced 1-byte string should not find U+0141")
        
        # Slice from 2-byte string
        s2 = L('héllo wörld')
        slice_result = s2[3:9]
        result = slice_result.findc(0x1F600)  # Emoji beyond 2-byte
        self.assertEqual(result, -1, "Sliced 2-byte string should not find emoji")
        
        # Verify valid search in slice
        result = slice_result.findc('o')
        self.assertGreaterEqual(result, 0, "Should find 'o' in slice")
        
        # Slice containing 'a' (0x41) - test potential collision
        s3 = L('banana')
        slice_with_a = s3[1:4]  # 'ana'
        result = slice_with_a.findc(0x0141)  # Should not match 'a'
        self.assertEqual(result, -1, "U+0141 should not match 'a' in slice")
        
        # Stepped slice
        s4 = L('hello')
        stepped = s4[::2]  # 'hlo'
        result = stepped.findc(0x0141)
        self.assertEqual(result, -1, "Stepped slice should not find U+0141")

    def test_unicode_kind_boundary_with_multiply(self):
        """Test that string multiplication preserves correct unicode_kind handling"""
        # Multiply 1-byte string
        s1 = L('abc')
        repeated = s1 * 3
        result = repeated.findc(0x0141)  # U+0141 beyond 1-byte
        self.assertEqual(result, -1, "Multiplied 1-byte string should not find U+0141")
        
        # Multiply 2-byte string
        s2 = L('hé')
        repeated2 = s2 * 5
        result = repeated2.findc(0x1F600)  # Emoji beyond 2-byte
        self.assertEqual(result, -1, "Multiplied 2-byte string should not find emoji")
        
        # Verify valid search in multiplied string
        result = repeated2.findc('é')
        self.assertGreaterEqual(result, 0, "Should find 'é' in multiplied string")
        
        # Multiply string with 'a' (0x41) - test collision
        s3 = L('ha')
        repeated3 = s3 * 4  # 'hahahaha'
        result = repeated3.findc(0x0141)  # Should not match 'a'
        self.assertEqual(result, -1, "U+0141 should not match 'a' in multiplied string")
        
        # rfindc on multiplied string
        result = repeated3.rfindc(0x0141)
        self.assertEqual(result, -1, "rfindc: U+0141 should not match 'a' in multiplied string")


if __name__ == '__main__':
    unittest.main()
