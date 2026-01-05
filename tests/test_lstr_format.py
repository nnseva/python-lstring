"""
Unit tests for str.format()-style formatting with lazy strings.
"""

import unittest
from lstring import L


class TestFormatAutoNumbered(unittest.TestCase):
    """Test auto-numbered placeholders ({})."""
    
    def test_simple_string(self):
        """Test simple {} formatting."""
        result = L('Hello {}').format('world')
        self.assertEqual(str(result), 'Hello world')
    
    def test_multiple_placeholders(self):
        """Test multiple {} placeholders."""
        result = L('{} {} {}').format('one', 'two', 'three')
        self.assertEqual(str(result), 'one two three')
    
    def test_with_format_spec(self):
        """Test {} with format spec."""
        result = L('Pi: {:.2f}').format(3.14159)
        self.assertEqual(str(result), 'Pi: 3.14')
    
    def test_with_conversion(self):
        """Test {} with conversion flags."""
        result = L('Value: {!r}').format('test')
        self.assertEqual(str(result), "Value: 'test'")
    
    def test_width_and_precision(self):
        """Test {} with width and precision."""
        result = L('{:10.2f}').format(3.14159)
        self.assertEqual(str(result), '      3.14')
    
    def test_alignment(self):
        """Test {} with alignment."""
        result = L('{:<10}').format('test')
        self.assertEqual(str(result), 'test      ')
    
    def test_zero_padding(self):
        """Test {} with zero padding."""
        result = L('{:05d}').format(42)
        self.assertEqual(str(result), '00042')


class TestFormatNumbered(unittest.TestCase):
    """Test numbered placeholders ({0}, {1})."""
    
    def test_simple_numbered(self):
        """Test simple {0} formatting."""
        result = L('Hello {0}').format('world')
        self.assertEqual(str(result), 'Hello world')
    
    def test_multiple_numbered(self):
        """Test multiple numbered placeholders."""
        result = L('{0} {1} {2}').format('one', 'two', 'three')
        self.assertEqual(str(result), 'one two three')
    
    def test_reordered(self):
        """Test reordered numbered placeholders."""
        result = L('{2} {0} {1}').format('one', 'two', 'three')
        self.assertEqual(str(result), 'three one two')
    
    def test_repeated(self):
        """Test repeated numbered placeholders."""
        result = L('{0} {1} {0}').format('hello', 'world')
        self.assertEqual(str(result), 'hello world hello')
    
    def test_with_format_spec(self):
        """Test {0} with format spec."""
        result = L('{0:.2f}').format(3.14159)
        self.assertEqual(str(result), '3.14')
    
    def test_mixed_order(self):
        """Test mixed order of numbered placeholders."""
        result = L('{1} + {0} = {2}').format(5, 3, 8)
        self.assertEqual(str(result), '3 + 5 = 8')


class TestFormatNamed(unittest.TestCase):
    """Test named placeholders ({name})."""
    
    def test_simple_named(self):
        """Test simple {name} formatting."""
        result = L('Hello {name}').format(name='world')
        self.assertEqual(str(result), 'Hello world')
    
    def test_multiple_named(self):
        """Test multiple named placeholders."""
        result = L('{greeting} {name}').format(greeting='Hello', name='Alice')
        self.assertEqual(str(result), 'Hello Alice')
    
    def test_repeated_named(self):
        """Test repeated named placeholders."""
        result = L('{x} + {x} = {y}').format(x=5, y=10)
        self.assertEqual(str(result), '5 + 5 = 10')
    
    def test_with_format_spec(self):
        """Test {name} with format spec."""
        result = L('{value:.2f}').format(value=3.14159)
        self.assertEqual(str(result), '3.14')
    
    def test_with_conversion(self):
        """Test {name} with conversion."""
        result = L('{value!r}').format(value='test')
        self.assertEqual(str(result), "'test'")
    
    def test_width_alignment(self):
        """Test {name} with width and alignment."""
        result = L('{name:>10}').format(name='test')
        self.assertEqual(str(result), '      test')


class TestFormatAttributeAccess(unittest.TestCase):
    """Test attribute and index access in placeholders."""
    
    def test_attribute_access(self):
        """Test {obj.attr} formatting."""
        class Obj:
            attr = 'value'
        result = L('{obj.attr}').format(obj=Obj())
        self.assertEqual(str(result), 'value')
    
    def test_nested_attribute(self):
        """Test {obj.attr.nested} formatting."""
        class Inner:
            nested = 'deep'
        class Outer:
            attr = Inner()
        result = L('{obj.attr.nested}').format(obj=Outer())
        self.assertEqual(str(result), 'deep')
    
    def test_dict_index(self):
        """Test {dict[key]} formatting."""
        result = L('{data[key]}').format(data={'key': 'value'})
        self.assertEqual(str(result), 'value')
    
    def test_list_index(self):
        """Test {list[0]} formatting."""
        result = L('{items[0]} {items[1]}').format(items=['first', 'second'])
        self.assertEqual(str(result), 'first second')
    
    def test_numbered_with_attribute(self):
        """Test {0.attr} formatting."""
        class Obj:
            attr = 'value'
        result = L('{0.attr}').format(Obj())
        self.assertEqual(str(result), 'value')
    
    def test_numbered_with_index(self):
        """Test {0[key]} formatting."""
        result = L('{0[key]}').format({'key': 'value'})
        self.assertEqual(str(result), 'value')


class TestFormatEscaping(unittest.TestCase):
    """Test escape sequences in format strings."""
    
    def test_double_open_brace(self):
        """Test {{ escape sequence."""
        result = L('{{escaped}}').format()
        self.assertEqual(str(result), '{escaped}')
    
    def test_double_close_brace(self):
        """Test }} escape sequence."""
        result = L('value}}').format()
        self.assertEqual(str(result), 'value}')
    
    def test_mixed_escapes_and_placeholders(self):
        """Test mixing escapes with placeholders."""
        result = L('{{{}}}').format('value')
        self.assertEqual(str(result), '{value}')
    
    def test_literal_braces_with_formatting(self):
        """Test literal braces around formatted values."""
        result = L('set: {{{0}, {1}}}').format(1, 2)
        self.assertEqual(str(result), 'set: {1, 2}')
    
    def test_percent_complete(self):
        """Test percentage with braces."""
        result = L('{percent}% complete').format(percent=100)
        self.assertEqual(str(result), '100% complete')


class TestFormatNested(unittest.TestCase):
    """Test nested placeholders in format specs."""
    
    def test_nested_width(self):
        """Test {value:{width}} formatting."""
        result = L('{value:{width}}').format(value='test', width=10)
        self.assertEqual(str(result), 'test      ')
    
    def test_nested_precision(self):
        """Test {value:.{precision}f} formatting."""
        result = L('{value:.{precision}f}').format(value=3.14159, precision=2)
        self.assertEqual(str(result), '3.14')
    
    def test_nested_width_and_precision(self):
        """Test {value:{width}.{precision}f} formatting."""
        result = L('{value:{width}.{precision}f}').format(
            value=3.14159, width=10, precision=2
        )
        self.assertEqual(str(result), '      3.14')
    
    def test_nested_with_alignment(self):
        """Test {value:>{width}} formatting."""
        result = L('{value:>{width}}').format(value='test', width=10)
        self.assertEqual(str(result), '      test')


class TestFormatMixedTypes(unittest.TestCase):
    """Test mixing positional and keyword arguments."""
    
    def test_named_with_positional_args(self):
        """Test named placeholders can coexist with positional args."""
        result = L('{name} {value}').format('ignored', name='Alice', value=42)
        self.assertEqual(str(result), 'Alice 42')
    
    def test_numbered_with_kwargs(self):
        """Test numbered placeholders with kwargs."""
        result = L('{0} {name}').format('first', name='second')
        self.assertEqual(str(result), 'first second')
    
    def test_auto_with_kwargs(self):
        """Test auto-numbered with kwargs."""
        result = L('{} {name}').format('first', name='second')
        self.assertEqual(str(result), 'first second')


class TestFormatErrors(unittest.TestCase):
    """Test error handling in format."""
    
    def test_cannot_mix_auto_and_numbered(self):
        """Test that mixing {} and {0} raises error."""
        with self.assertRaises(ValueError):
            L('{} {0}').format('a', 'b')
    
    def test_cannot_mix_numbered_and_auto(self):
        """Test that mixing {0} and {} raises error."""
        with self.assertRaises(ValueError):
            L('{0} {}').format('a', 'b')


class TestFormatEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def test_empty_string(self):
        """Test formatting empty string."""
        result = L('').format()
        self.assertEqual(str(result), '')
    
    def test_no_placeholders(self):
        """Test string with no placeholders."""
        result = L('plain text').format()
        self.assertEqual(str(result), 'plain text')
    
    def test_only_literals(self):
        """Test string with only literal braces."""
        result = L('{{}}').format()
        self.assertEqual(str(result), '{}')
    
    def test_empty_placeholder(self):
        """Test empty {} placeholder."""
        result = L('{}').format('value')
        self.assertEqual(str(result), 'value')
    
    def test_int_formatting(self):
        """Test integer formatting."""
        result = L('{:d}').format(42)
        self.assertEqual(str(result), '42')
    
    def test_hex_formatting(self):
        """Test hexadecimal formatting."""
        result = L('{:x}').format(255)
        self.assertEqual(str(result), 'ff')
    
    def test_hex_uppercase(self):
        """Test uppercase hexadecimal."""
        result = L('{:X}').format(255)
        self.assertEqual(str(result), 'FF')
    
    def test_binary_formatting(self):
        """Test binary formatting."""
        result = L('{:b}').format(5)
        self.assertEqual(str(result), '101')
    
    def test_octal_formatting(self):
        """Test octal formatting."""
        result = L('{:o}').format(8)
        self.assertEqual(str(result), '10')
    
    def test_scientific_notation(self):
        """Test scientific notation."""
        result = L('{:.2e}').format(1234.5)
        self.assertEqual(str(result), '1.23e+03')
    
    def test_percentage(self):
        """Test percentage formatting."""
        result = L('{:.1%}').format(0.5)
        self.assertEqual(str(result), '50.0%')
    
    def test_thousands_separator(self):
        """Test thousands separator."""
        result = L('{:,}').format(1000000)
        self.assertEqual(str(result), '1,000,000')
    
    def test_sign_formatting(self):
        """Test sign formatting."""
        result = L('{:+d} {:+d}').format(42, -42)
        self.assertEqual(str(result), '+42 -42')
    
    def test_lazy_preservation(self):
        """Test that static parts remain lazy."""
        base = L('prefix_') + L('middle') + L('_suffix')
        result = base + L(' {} {}').format('test', 42)
        self.assertEqual(str(result), 'prefix_middle_suffix test 42')


class TestFormatComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""
    
    def test_table_row(self):
        """Test formatting a table row."""
        result = L('{name:<10} {age:>3} {score:6.2f}').format(
            name='Alice', age=30, score=95.5
        )
        self.assertEqual(str(result), 'Alice       30  95.50')
    
    def test_log_message(self):
        """Test formatting a log message."""
        result = L('[{level}] {message} (code={code:04d})').format(
            level='ERROR', message='Connection failed', code=42
        )
        self.assertEqual(str(result), '[ERROR] Connection failed (code=0042)')
    
    def test_template_with_nested_data(self):
        """Test template with nested object access."""
        class User:
            def __init__(self, name, age):
                self.name = name
                self.age = age
        
        result = L('User: {user.name}, Age: {user.age}').format(
            user=User('Bob', 25)
        )
        self.assertEqual(str(result), 'User: Bob, Age: 25')
    
    def test_multiple_conversions(self):
        """Test multiple conversion types."""
        result = L('{0!s} {0!r} {0!a}').format('test')
        self.assertEqual(str(result), "test 'test' 'test'")
    
    def test_fill_and_align(self):
        """Test fill character with alignment."""
        result = L('{:*>10}').format('test')
        self.assertEqual(str(result), '******test')


if __name__ == '__main__':
    unittest.main()
