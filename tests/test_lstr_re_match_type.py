import unittest
from lstring import L
import lstring.re as lre

class TestMatchReturnType(unittest.TestCase):

    def setUp(self):
        self.pattern = lre.compile(r'(a)(b)(?P<name>c)')
        self.subject_str = 'abc'
        self.subject_L = L('abc')

    def test_group_type_subclass(self):
        class MyL(L):
            pass
        subject = MyL('abc')
        m = self.pattern.match(subject)
        self.assertIsNotNone(m)
        expected_type = type(subject)
        # group(0), group(1), group('name')
        self.assertIs(type(m.group(0)), expected_type)
        self.assertIs(type(m.group(1)), expected_type)
        self.assertIs(type(m.group('name')), expected_type)
        # groups() returns tuple of MyL
        self.assertTrue(all(type(g) is expected_type for g in m.groups()))
        # __getitem__
        self.assertIs(type(m[0]), expected_type)
        self.assertIs(type(m['name']), expected_type)

        # Аргумент group может быть как str, так и экземпляром того же подкласса
        self.assertIs(type(m.group(MyL('name'))), expected_type)
        self.assertEqual(m.group('name'), m.group(MyL('name')))


    def test_group_type_str(self):
        m = self.pattern.match(self.subject_str)
        self.assertIsNotNone(m)
        # NB: Even if subject is str, it is converted to L in Match.__init__
        expected_type = type(self.subject_L)
        # group(0), group(1), group('name')
        self.assertIs(type(m.group(0)), expected_type)
        self.assertIs(type(m.group(1)), expected_type)
        self.assertIs(type(m.group('name')), expected_type)
        # groups() returns tuple of L
        self.assertTrue(all(type(g) is expected_type for g in m.groups()))
        # __getitem__
        self.assertIs(type(m[0]), expected_type)
        self.assertIs(type(m['name']), expected_type)

    def test_group_type_L(self):
        m = self.pattern.match(self.subject_L)
        self.assertIsNotNone(m)
        # group(0), group(1), group('name')
        self.assertIs(type(m.group(0)), type(self.subject_L))
        self.assertIs(type(m.group(1)), type(self.subject_L))
        self.assertIs(type(m.group('name')), type(self.subject_L))
        # groups() returns tuple of L
        self.assertTrue(all(type(g) is type(self.subject_L) for g in m.groups()))
        # __getitem__
        self.assertIs(type(m[0]), type(self.subject_L))
        self.assertIs(type(m['name']), type(self.subject_L))

    def test_span_start_end_types(self):
        # These always return ints, regardless of subject type
        mL = self.pattern.match(self.subject_L)
        ms = self.pattern.match(self.subject_str)
        for m in (mL, ms):
            self.assertIsInstance(m.start(), int)
            self.assertIsInstance(m.end(), int)
            self.assertIsInstance(m.span(), tuple)
            self.assertEqual(len(m.span()), 2)
            self.assertTrue(all(isinstance(x, int) for x in m.span()))

    def test_where_attribute_L_identity(self):
        subject = self.subject_L
        m = self.pattern.match(subject)
        self.assertIsNotNone(m)
        self.assertTrue(hasattr(m, 'where'))
        self.assertIs(m.where, subject)
        self.assertIs(type(m.where), type(subject))

        with self.assertRaises(AttributeError):
            m.where = subject

    def test_where_attribute_subclass_identity(self):
        class MyL(L):
            pass

        subject = MyL('abc')
        m = self.pattern.match(subject)
        self.assertIsNotNone(m)
        self.assertIs(m.where, subject)
        self.assertIs(type(m.where), type(subject))

    def test_where_attribute_str_subject_converted(self):
        m = self.pattern.match(self.subject_str)
        self.assertIsNotNone(m)
        # str subject is converted to L in Python wrapper, so m.where is an L instance
        self.assertIsInstance(m.where, L)
        self.assertIs(type(m.where), type(self.subject_L))
        self.assertEqual(str(m.where), self.subject_str)

if __name__ == '__main__':
    unittest.main()
