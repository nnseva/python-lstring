"""
Unit tests for f-string style formatting with lazy strings.
"""

import unittest
from lstring import L
from lstring.format import fformat


class TestFFormatBasic(unittest.TestCase):
    """Test basic fformat functionality with explicit context."""
    
    def test_simple_variable(self):
        """Test simple variable substitution."""
        x = 42
        result = fformat(L('Value: {x}'), globals(), locals())
        self.assertEqual(str(result), 'Value: 42')
    
    def test_arithmetic_expression(self):
        """Test arithmetic expression evaluation."""
        x = 10
        y = 5
        result = fformat(L('Sum: {x + y}'), globals(), locals())
        self.assertEqual(str(result), 'Sum: 15')
    
    def test_method_call(self):
        """Test method call on variable."""
        name = 'alice'
        result = fformat(L('Name: {name.upper()}'), globals(), locals())
        self.assertEqual(str(result), 'Name: ALICE')
    
    def test_function_call(self):
        """Test function call with arguments."""
        numbers = [1, 2, 3, 4, 5]
        result = fformat(L('Sum: {sum(numbers)}'), globals(), locals())
        self.assertEqual(str(result), 'Sum: 15')
    
    def test_attribute_access(self):
        """Test attribute access."""
        class Obj:
            value = 42
        obj = Obj()
        result = fformat(L('Value: {obj.value}'), globals(), locals())
        self.assertEqual(str(result), 'Value: 42')
    
    def test_indexing(self):
        """Test list/dict indexing."""
        data = {'key': 'value'}
        result = fformat(L('Data: {data["key"]}'), globals(), locals())
        self.assertEqual(str(result), 'Data: value')
    
    def test_multiple_expressions(self):
        """Test multiple expressions in one string."""
        x = 10
        y = 20
        z = 30
        result = fformat(L('{x}, {y}, {z}'), globals(), locals())
        self.assertEqual(str(result), '10, 20, 30')
    
    def test_empty_expression_error(self):
        """Test that empty {} raises an error."""
        with self.assertRaises(SyntaxError):
            fformat(L('Empty: {}'), globals(), locals())


class TestFFormatConversions(unittest.TestCase):
    """Test conversion flags (!r, !s, !a)."""
    
    def test_repr_conversion(self):
        """Test !r conversion."""
        value = 'test'
        result = fformat(L('Repr: {value!r}'), globals(), locals())
        self.assertEqual(str(result), "Repr: 'test'")
    
    def test_str_conversion(self):
        """Test !s conversion."""
        value = 42
        result = fformat(L('Str: {value!s}'), globals(), locals())
        self.assertEqual(str(result), 'Str: 42')
    
    def test_ascii_conversion(self):
        """Test !a conversion."""
        value = 'привет'
        result = fformat(L('ASCII: {value!a}'), globals(), locals())
        self.assertEqual(str(result), "ASCII: '\\u043f\\u0440\\u0438\\u0432\\u0435\\u0442'")
    
    def test_repr_with_expression(self):
        """Test !r with expression."""
        x = 5
        result = fformat(L('Repr: {x * 2!r}'), globals(), locals())
        self.assertEqual(str(result), 'Repr: 10')


class TestFFormatSpecs(unittest.TestCase):
    """Test format specifications."""
    
    def test_float_precision(self):
        """Test float precision formatting."""
        pi = 3.14159
        result = fformat(L('Pi: {pi:.2f}'), globals(), locals())
        self.assertEqual(str(result), 'Pi: 3.14')
    
    def test_integer_width(self):
        """Test integer width formatting."""
        x = 42
        result = fformat(L('Value: {x:>5}'), globals(), locals())
        self.assertEqual(str(result), 'Value:    42')
    
    def test_string_alignment(self):
        """Test string alignment."""
        name = 'test'
        result = fformat(L('Left: {name:<10}'), globals(), locals())
        self.assertEqual(str(result), 'Left: test      ')
    
    def test_zero_padding(self):
        """Test zero padding."""
        num = 7
        result = fformat(L('Padded: {num:04d}'), globals(), locals())
        self.assertEqual(str(result), 'Padded: 0007')
    
    def test_hex_format(self):
        """Test hexadecimal format."""
        value = 255
        result = fformat(L('Hex: {value:#x}'), globals(), locals())
        self.assertEqual(str(result), 'Hex: 0xff')
    
    def test_percentage(self):
        """Test percentage format."""
        ratio = 0.75
        result = fformat(L('Percent: {ratio:.1%}'), globals(), locals())
        self.assertEqual(str(result), 'Percent: 75.0%')


class TestFFormatConversionWithSpec(unittest.TestCase):
    """Test combination of conversions and format specs."""
    
    def test_repr_with_width(self):
        """Test !r with width specification."""
        name = 'alice'
        result = fformat(L('Name: {name!r:>10}'), globals(), locals())
        self.assertEqual(str(result), "Name:    'alice'")
    
    def test_str_with_alignment(self):
        """Test !s with alignment."""
        value = 42
        result = fformat(L('Value: {value!s:<5}'), globals(), locals())
        self.assertEqual(str(result), 'Value: 42   ')


class TestFFormatLiterals(unittest.TestCase):
    """Test literal braces."""
    
    def test_double_open_brace(self):
        """Test {{ becomes {."""
        result = fformat(L('Literal: {{'), globals(), locals())
        self.assertEqual(str(result), 'Literal: {')
    
    def test_double_close_brace(self):
        """Test }} becomes }."""
        result = fformat(L('Literal: }}'), globals(), locals())
        self.assertEqual(str(result), 'Literal: }')
    
    def test_both_literal_braces(self):
        """Test {{ and }} together."""
        result = fformat(L('Set: {{1, 2}}'), globals(), locals())
        self.assertEqual(str(result), 'Set: {1, 2}')
    
    def test_literal_with_expression(self):
        """Test literal braces mixed with expressions."""
        x = 42
        result = fformat(L('Dict: {{"key": {x}}}'), globals(), locals())
        self.assertEqual(str(result), 'Dict: {"key": 42}')


class TestFFormatNamespaces(unittest.TestCase):
    """Test explicit namespace handling."""
    
    def test_custom_globals(self):
        """Test with custom globals dict."""
        custom_globals = {'x': 100, 'y': 200}
        result = fformat(L('Sum: {x + y}'), custom_globals, {})
        self.assertEqual(str(result), 'Sum: 300')
    
    def test_custom_locals(self):
        """Test with custom locals dict."""
        custom_locals = {'name': 'Bob'}
        result = fformat(L('Name: {name.upper()}'), {}, custom_locals)
        self.assertEqual(str(result), 'Name: BOB')
    
    def test_both_namespaces(self):
        """Test with both custom globals and locals."""
        custom_globals = {'x': 10}
        custom_locals = {'y': 20}
        result = fformat(L('Result: {x + y}'), custom_globals, custom_locals)
        self.assertEqual(str(result), 'Result: 30')
    
    def test_locals_shadow_globals(self):
        """Test that locals shadow globals."""
        custom_globals = {'x': 10}
        custom_locals = {'x': 20}
        result = fformat(L('Value: {x}'), custom_globals, custom_locals)
        self.assertEqual(str(result), 'Value: 20')


class TestFFormatErrors(unittest.TestCase):
    """Test error handling."""
    
    def test_undefined_variable(self):
        """Test error on undefined variable."""
        with self.assertRaises(NameError) as cm:
            fformat(L('Value: {undefined_var}'), {}, {})
        self.assertIn('undefined_var', str(cm.exception))
    
    def test_syntax_error(self):
        """Test error on syntax error in expression."""
        with self.assertRaises(SyntaxError):
            fformat(L('Bad: {x +}'), {'x': 10}, {})
    
    def test_invalid_format_spec(self):
        """Test error on invalid format spec."""
        x = 'string'
        with self.assertRaises(ValueError):
            fformat(L('Bad: {x:.2f}'), globals(), locals())


class TestLMethodF(unittest.TestCase):
    """Test L.f() method with implicit context."""
    
    def test_simple_variable_implicit(self):
        """Test simple variable with implicit context."""
        x = 42
        result = L('Value: {x}').f()
        self.assertEqual(str(result), 'Value: 42')
    
    def test_expression_implicit(self):
        """Test expression with implicit context."""
        a = 10
        b = 20
        result = L('Sum: {a + b}').f()
        self.assertEqual(str(result), 'Sum: 30')
    
    def test_method_call_implicit(self):
        """Test method call with implicit context."""
        text = 'hello'
        result = L('Upper: {text.upper()}').f()
        self.assertEqual(str(result), 'Upper: HELLO')
    
    def test_function_call_implicit(self):
        """Test function call with implicit context."""
        nums = [1, 2, 3]
        result = L('Max: {max(nums)}').f()
        self.assertEqual(str(result), 'Max: 3')
    
    def test_conversion_implicit(self):
        """Test conversion with implicit context."""
        value = 'test'
        result = L('Repr: {value!r}').f()
        self.assertEqual(str(result), "Repr: 'test'")
    
    def test_format_spec_implicit(self):
        """Test format spec with implicit context."""
        pi = 3.14159
        result = L('Pi: {pi:.2f}').f()
        self.assertEqual(str(result), 'Pi: 3.14')
    
    def test_literals_implicit(self):
        """Test literal braces with implicit context."""
        x = 10
        result = L('Set: {{{x}}}').f()
        self.assertEqual(str(result), 'Set: {10}')


class TestLMethodFExplicit(unittest.TestCase):
    """Test L.f() method with explicit context."""
    
    def test_explicit_globals(self):
        """Test L.f() with explicit globals."""
        custom_globals = {'x': 99}
        result = L('Value: {x}').f(custom_globals, {})
        self.assertEqual(str(result), 'Value: 99')
    
    def test_explicit_locals(self):
        """Test L.f() with explicit locals."""
        custom_locals = {'name': 'Charlie'}
        result = L('Name: {name}').f({}, custom_locals)
        self.assertEqual(str(result), 'Name: Charlie')
    
    def test_explicit_both(self):
        """Test L.f() with both explicit namespaces."""
        custom_globals = {'mult': lambda x, y: x * y}
        custom_locals = {'a': 5, 'b': 7}
        result = L('Product: {mult(a, b)}').f(custom_globals, custom_locals)
        self.assertEqual(str(result), 'Product: 35')


class TestFFormatComplexExpressions(unittest.TestCase):
    """Test complex expressions."""
    
    def test_nested_calls(self):
        """Test nested function calls."""
        data = [[1, 2], [3, 4], [5, 6]]
        result = fformat(L('Max: {max(max(row) for row in data)}'), globals(), locals())
        self.assertEqual(str(result), 'Max: 6')
    
    def test_list_comprehension(self):
        """Test list comprehension."""
        nums = [1, 2, 3, 4, 5]
        result = fformat(L('Even: {[x for x in nums if x % 2 == 0]}'), globals(), locals())
        self.assertEqual(str(result), 'Even: [2, 4]')
    
    def test_conditional_expression(self):
        """Test conditional (ternary) expression."""
        x = 10
        result = fformat(L('Result: {("even" if x % 2 == 0 else "odd")}'), globals(), locals())
        self.assertEqual(str(result), 'Result: even')
    
    def test_string_operations(self):
        """Test string operations in expression."""
        prefix = 'Hello'
        suffix = 'World'
        result = fformat(L('Combined: {prefix + " " + suffix}'), globals(), locals())
        self.assertEqual(str(result), 'Combined: Hello World')
    
    def test_dict_literal(self):
        """Test dict literal in expression."""
        key = 'name'
        value = 'Alice'
        result = fformat(L('Dict: {{"{key}": "{value}"}}'), globals(), locals())
        self.assertIn('name', str(result))
        self.assertIn('Alice', str(result))


class TestFFormatEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def test_empty_string(self):
        """Test formatting empty string."""
        result = fformat(L(''), globals(), locals())
        self.assertEqual(str(result), '')
    
    def test_no_placeholders(self):
        """Test string with no placeholders."""
        result = fformat(L('Just text'), globals(), locals())
        self.assertEqual(str(result), 'Just text')
    
    def test_only_literals(self):
        """Test string with only literal braces."""
        result = fformat(L('{{}}'), globals(), locals())
        self.assertEqual(str(result), '{}')
    
    def test_return_type_is_L(self):
        """Test that result is L instance."""
        x = 42
        result = fformat(L('Value: {x}'), globals(), locals())
        self.assertIsInstance(result, L)
    
    def test_nested_braces_in_string(self):
        """Test nested braces in string literals."""
        data = {'a': 1}
        result = fformat(L('Data: {data}'), globals(), locals())
        self.assertIn('a', str(result))
        self.assertIn('1', str(result))


if __name__ == '__main__':
    unittest.main()
