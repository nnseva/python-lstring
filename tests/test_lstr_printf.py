"""
Unit tests for printf-style formatting (% operator) with lazy strings.
"""

import unittest
from lstring import L


class TestPrintfPositional(unittest.TestCase):
    """Test positional (tuple-based) printf formatting."""
    
    def test_simple_string(self):
        """Test simple %s formatting."""
        result = L('Hello %s') % ('world',)
        self.assertEqual(str(result), 'Hello world')
    
    def test_single_value_no_tuple(self):
        """Test formatting with single value (not in tuple)."""
        result = L('Hello %s') % 'world'
        self.assertEqual(str(result), 'Hello world')
    
    def test_integer_formatting(self):
        """Test %d integer formatting."""
        result = L('Answer: %d') % (42,)
        self.assertEqual(str(result), 'Answer: 42')
    
    def test_float_formatting(self):
        """Test %f float formatting."""
        result = L('Pi: %f') % (3.14159,)
        self.assertEqual(str(result), 'Pi: 3.141590')
    
    def test_float_precision(self):
        """Test %.Nf precision formatting."""
        result = L('Pi: %.2f') % (3.14159,)
        self.assertEqual(str(result), 'Pi: 3.14')
    
    def test_percent_escape(self):
        """Test %% escape sequence."""
        result = L('100%% complete') % ()
        self.assertEqual(str(result), '100% complete')
    
    def test_multiple_placeholders(self):
        """Test multiple placeholders in one string."""
        result = L('%s: %d items, %.2f total') % ('Order', 5, 123.456)
        self.assertEqual(str(result), 'Order: 5 items, 123.46 total')
    
    def test_width_specifier(self):
        """Test width specifier."""
        result = L('%10s') % ('test',)
        self.assertEqual(str(result), '      test')
    
    def test_zero_padding(self):
        """Test zero-padding with 0 flag."""
        result = L('%05d') % (42,)
        self.assertEqual(str(result), '00042')
    
    def test_left_align(self):
        """Test left-alignment with - flag."""
        result = L('%-10s') % ('test',)
        self.assertEqual(str(result), 'test      ')
    
    def test_wildcard_width(self):
        """Test * wildcard for width."""
        result = L('%*s') % (10, 'test')
        self.assertEqual(str(result), '      test')
    
    def test_wildcard_precision(self):
        """Test * wildcard for precision."""
        result = L('%.*f') % (2, 3.14159)
        self.assertEqual(str(result), '3.14')
    
    def test_wildcard_width_and_precision(self):
        """Test both * wildcards."""
        result = L('%*.*f') % (10, 2, 3.14159)
        self.assertEqual(str(result), '      3.14')
    
    def test_hex_formatting(self):
        """Test hexadecimal formatting."""
        result = L('0x%x') % (255,)
        self.assertEqual(str(result), '0xff')
    
    def test_uppercase_hex(self):
        """Test uppercase hexadecimal formatting."""
        result = L('0x%X') % (255,)
        self.assertEqual(str(result), '0xFF')
    
    def test_octal_formatting(self):
        """Test octal formatting."""
        result = L('%o') % (64,)
        self.assertEqual(str(result), '100')
    
    def test_scientific_notation(self):
        """Test scientific notation."""
        result = L('%.2e') % (1234.5,)
        self.assertEqual(str(result), '1.23e+03')
    
    def test_repr_formatting(self):
        """Test %r repr formatting."""
        result = L('%r') % ('test',)
        self.assertEqual(str(result), "'test'")
    
    def test_mixed_static_and_formatted(self):
        """Test that static parts remain lazy."""
        # Create a string with static prefix and suffix
        base = L('prefix_') + L('middle') + L('_suffix')
        result = base + L(' %s %d') % ('test', 42)
        self.assertEqual(str(result), 'prefix_middle_suffix test 42')


class TestPrintfNamed(unittest.TestCase):
    """Test named (dict-based) printf formatting."""
    
    def test_simple_string(self):
        """Test simple %(name)s formatting."""
        result = L('Hello %(name)s') % {'name': 'world'}
        self.assertEqual(str(result), 'Hello world')
    
    def test_str_keys(self):
        """Test formatting with str keys in dict."""
        result = L('%(greeting)s %(name)s') % {'greeting': 'Hello', 'name': 'Alice'}
        self.assertEqual(str(result), 'Hello Alice')
    
    def test_L_keys(self):
        """Test formatting with L keys in dict."""
        result = L('%(greeting)s %(name)s') % {L('greeting'): 'Hi', L('name'): 'Bob'}
        self.assertEqual(str(result), 'Hi Bob')
    
    def test_mixed_keys(self):
        """Test formatting with mixed str and L keys in dict."""
        result = L('%(a)s %(b)s') % {'a': 'first', L('b'): 'second'}
        self.assertEqual(str(result), 'first second')
    
    def test_integer_formatting(self):
        """Test %(name)d integer formatting."""
        result = L('Age: %(age)d') % {'age': 42}
        self.assertEqual(str(result), 'Age: 42')
    
    def test_float_formatting(self):
        """Test %(name)f float formatting."""
        result = L('Price: %(price)f') % {'price': 19.99}
        self.assertEqual(str(result), 'Price: 19.990000')
    
    def test_float_precision(self):
        """Test %(name).Nf precision formatting."""
        result = L('Pi: %(pi).2f') % {'pi': 3.14159}
        self.assertEqual(str(result), 'Pi: 3.14')
    
    def test_percent_escape(self):
        """Test %% escape sequence."""
        result = L('%(pct)d%% complete') % {'pct': 100}
        self.assertEqual(str(result), '100% complete')
    
    def test_multiple_placeholders(self):
        """Test multiple named placeholders."""
        result = L('%(item)s: %(count)d items, %(total).2f total') % {
            'item': 'Order',
            'count': 5,
            'total': 123.456
        }
        self.assertEqual(str(result), 'Order: 5 items, 123.46 total')
    
    def test_width_specifier(self):
        """Test width specifier with named placeholder."""
        result = L('%(name)10s') % {'name': 'test'}
        self.assertEqual(str(result), '      test')
    
    def test_zero_padding(self):
        """Test zero-padding with named placeholder."""
        result = L('%(num)05d') % {'num': 42}
        self.assertEqual(str(result), '00042')
    
    def test_left_align(self):
        """Test left-alignment with named placeholder."""
        result = L('%(name)-10s') % {'name': 'test'}
        self.assertEqual(str(result), 'test      ')
    
    def test_hex_formatting(self):
        """Test hexadecimal formatting."""
        result = L('0x%(num)x') % {'num': 255}
        self.assertEqual(str(result), '0xff')
    
    def test_uppercase_hex(self):
        """Test uppercase hexadecimal formatting."""
        result = L('0x%(num)X') % {'num': 255}
        self.assertEqual(str(result), '0xFF')
    
    def test_octal_formatting(self):
        """Test octal formatting."""
        result = L('%(num)o') % {'num': 64}
        self.assertEqual(str(result), '100')
    
    def test_scientific_notation(self):
        """Test scientific notation."""
        result = L('%(val).2e') % {'val': 1234.5}
        self.assertEqual(str(result), '1.23e+03')
    
    def test_repr_formatting(self):
        """Test %(name)r repr formatting."""
        result = L('%(text)r') % {'text': 'test'}
        self.assertEqual(str(result), "'test'")
    
    def test_same_name_multiple_times(self):
        """Test using the same name multiple times."""
        result = L('%(x)d + %(x)d = %(y)d') % {'x': 5, 'y': 10}
        self.assertEqual(str(result), '5 + 5 = 10')
    
    def test_mixed_static_and_formatted(self):
        """Test that static parts remain lazy."""
        base = L('prefix_') + L('middle') + L('_suffix')
        result = base + L(' %(name)s %(num)d') % {'name': 'test', 'num': 42}
        self.assertEqual(str(result), 'prefix_middle_suffix test 42')


if __name__ == '__main__':
    unittest.main()
