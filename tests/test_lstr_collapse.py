import unittest
import lstring

class TestLStrCollapse(unittest.TestCase):

    def setUp(self):
        # Ensure tests run with optimization disabled to preserve lazy buffer behavior
        lstring.set_optimize_threshold(0)

    def test_collapse_strbuffer_noop(self):
        s = lstring._lstr("hello")
        # should be a no-op and return None
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "hello")
        # hash should be preserved
        self.assertEqual(before_hash, hash(s))
        # repr for StrBuffer-backed objects starts with 'l' + repr(str)
        self.assertEqual(repr(s), before_repr)
        # idempotent
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "hello")

    def test_collapse_joinbuffer(self):
        a = lstring._lstr("foo")
        b = lstring._lstr("bar")
        s = a + b   # JoinBuffer backing
        self.assertEqual(str(s), "foobar")
        before_hash = hash(s)
        before_repr = repr(s)
        # repr before collapse should reflect the join expression
        self.assertIn("+", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "foobar")
        # hash preserved
        self.assertEqual(before_hash, hash(s))
        # repr after collapse should be 'l' + repr of the joined string
        self.assertEqual(repr(s), "l" + repr("foobar"))
        # idempotent
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "foobar")

    def test_collapse_slice1buffer(self):
        s0 = lstring._lstr("012345")
        s = s0[1:4]   # Slice1Buffer (step == 1)
        self.assertEqual(str(s), "123")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn(":", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "123")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "l" + repr("123"))

    def test_collapse_slicebuffer_step(self):
        s0 = lstring._lstr("0123456789")
        s = s0[::2]   # SliceBuffer (step != 1)
        self.assertEqual(str(s), "02468")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn(":", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "02468")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "l" + repr("02468"))

    def test_collapse_mulbuffer(self):
        s0 = lstring._lstr("ab")
        s = s0 * 4   # MulBuffer
        self.assertEqual(str(s), "abababab")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn("*", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "abababab")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "l" + repr("abababab"))

if __name__ == '__main__':
    unittest.main()
