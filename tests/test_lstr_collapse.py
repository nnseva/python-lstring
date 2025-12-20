import unittest
import lstring

class TestLStrCollapse(unittest.TestCase):
    """Tests for the collapse() behavior of various lazy Buffer implementations.

    The class verifies that collapsing lazy views (JoinBuffer, SliceBuffer,
    MulBuffer) produces concrete Python strings while preserving hash and
    expected representations.
    """

    @classmethod
    def setUpClass(cls):
        """Disable optimization for predictable lazy-buffer behavior."""
        cls.original_threshold = lstring.get_optimize_threshold()
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        """Restore optimization threshold after tests."""
        lstring.set_optimize_threshold(cls.original_threshold)


    def test_collapse_strbuffer_noop(self):
        """Collapsing a buffer already backed by a Python str is a no-op.

        The method should return None, leave the string value unchanged,
        and preserve the object's hash and repr.
        """
        s = lstring.L("hello")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "hello")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), before_repr)
        # idempotent
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "hello")

    def test_collapse_joinbuffer(self):
        """Collapsing a JoinBuffer should produce a concrete str equal to the concatenation.

        The repr before collapse should show the join expression; after collapse
        repr should be the canonical str repr prefixed with 'L'. Hash must be preserved.
        """
        a = lstring.L("foo")
        b = lstring.L("bar")
        s = a + b
        self.assertEqual(str(s), "foobar")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn("+", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "foobar")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "L" + repr("foobar"))
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "foobar")

    def test_collapse_slice1buffer(self):
        """Continuous slice (step==1) collapses into the expected substring.

        Verifies value, preserved hash, and final repr.
        """
        s0 = lstring.L("012345")
        s = s0[1:4]
        self.assertEqual(str(s), "123")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn(":", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "123")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "L" + repr("123"))

    def test_collapse_slicebuffer_step(self):
        """Strided slice collapses into the expected str of selected characters."""
        s0 = lstring.L("0123456789")
        s = s0[::2]
        self.assertEqual(str(s), "02468")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn(":", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "02468")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "L" + repr("02468"))

    def test_collapse_mulbuffer(self):
        """Repetition buffer collapses into repeated concrete string and preserves hash."""
        s0 = lstring.L("ab")
        s = s0 * 4
        self.assertEqual(str(s), "abababab")
        before_hash = hash(s)
        before_repr = repr(s)
        self.assertIn("*", before_repr)
        self.assertIsNone(s.collapse())
        self.assertEqual(str(s), "abababab")
        self.assertEqual(before_hash, hash(s))
        self.assertEqual(repr(s), "L" + repr("abababab"))

if __name__ == '__main__':
    unittest.main()
