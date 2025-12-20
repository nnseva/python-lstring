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


if __name__ == '__main__':
    unittest.main()
