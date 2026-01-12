import math
import unittest

import lstring
from lstring import L


def _repr_join_height(s: str) -> int:
    """Compute the height of the JoinBuffer tree from repr(s).

    We treat any non "+" node as a leaf (height=1).
    """

    def parse_height(expr: str) -> int:
        expr = expr.strip()
        if len(expr) >= 2 and expr[0] == "(" and expr[-1] == ")":
            inner = expr[1:-1]
            split = _split_top_level_plus(inner)
            if split is not None:
                left, right = split
                return 1 + max(parse_height(left), parse_height(right))
        return 1

    return parse_height(s)


def _split_top_level_plus(inner: str):
    """Split '(left + right)' inner content on the top-level ' + '.

    Returns (left, right) or None.
    """
    paren = 0
    bracket = 0
    in_str = False
    escape = False

    i = 0
    while i < len(inner):
        ch = inner[i]

        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "'":
                in_str = False
            i += 1
            continue

        if ch == "'":
            in_str = True
            i += 1
            continue

        if ch == "(":
            paren += 1
        elif ch == ")":
            paren -= 1
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket -= 1

        if paren == 0 and bracket == 0:
            if inner.startswith(" + ", i):
                return inner[:i], inner[i + 3 :]

        i += 1

    return None


class TestBalancedConcatRepr(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._orig_thresh = lstring.get_optimize_threshold()
        # disable C-level automatic collapsing/optimization for deterministic repr structure
        lstring.set_optimize_threshold(0)

    @classmethod
    def tearDownClass(cls):
        lstring.set_optimize_threshold(cls._orig_thresh)

    def test_many_simple_additions_balanced(self):
        n = 256
        parts = [L(str(i)) for i in range(n)]

        acc = parts[0]
        for p in parts[1:]:
            acc = acc + p

        self.assertEqual(str(acc), "".join(str(i) for i in range(n)))

        h = _repr_join_height(repr(acc))
        # A balanced binary tree over n leaves has height O(log2 n).
        # We allow a generous constant factor to avoid brittle expectations.
        self.assertLessEqual(h, 2 * math.ceil(math.log2(n)) + 3)

    def test_mixed_complex_operands_balanced(self):
        # Build leaves that are not JoinBuffers themselves (mul + slice)
        def complex_leaf(i: int) -> L:
            base = L("abcdefghijklmnopqrstuvwxyz") * (i % 5 + 2)
            return base[1: 1 + (i % 10 + 5)]

        n = 128
        parts = [complex_leaf(i) if (i % 3 == 0) else L(str(i)) for i in range(n)]

        acc = parts[0]
        for p in parts[1:]:
            acc = acc + p

        self.assertEqual(str(acc), "".join(str(x) for x in parts))

        h = _repr_join_height(repr(acc))
        self.assertLessEqual(h, 2 * math.ceil(math.log2(n)) + 3)


if __name__ == "__main__":
    unittest.main()
