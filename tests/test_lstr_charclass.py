#!/usr/bin/env python3
"""
Тесты для методов определения классов символов в L.
"""

import unittest
from lstring import L


class TestLStrCharacterClasses(unittest.TestCase):
    """Тесты для методов определения классов символов."""
    
    def test_isspace_whitespace(self):
        """Только пробельные символы возвращают True."""
        self.assertTrue(L(' \t\n\r\f\v').isspace())
        self.assertTrue(L('   ').isspace())
        self.assertTrue(L('\t').isspace())
        
    def test_isspace_mixed(self):
        """Смешанные символы возвращают False."""
        self.assertFalse(L('abc').isspace())
        self.assertFalse(L(' a ').isspace())
        self.assertFalse(L('').isspace())
        
    def test_isalpha_only_letters(self):
        """Только буквы возвращают True."""
        self.assertTrue(L('abc').isalpha())
        self.assertTrue(L('ABC').isalpha())
        self.assertTrue(L('абв').isalpha())
        
    def test_isalpha_mixed(self):
        """Смешанные символы возвращают False."""
        self.assertFalse(L('abc123').isalpha())
        self.assertFalse(L('a b').isalpha())
        self.assertFalse(L('').isalpha())
        
    def test_isdigit_only_digits(self):
        """Только цифры возвращают True."""
        self.assertTrue(L('123').isdigit())
        self.assertTrue(L('0').isdigit())
        
    def test_isdigit_mixed(self):
        """Смешанные символы возвращают False."""
        self.assertFalse(L('12a').isdigit())
        self.assertFalse(L('1 2').isdigit())
        self.assertFalse(L('').isdigit())
        
    def test_isalnum_alphanumeric(self):
        """Буквы и цифры возвращают True."""
        self.assertTrue(L('abc123').isalnum())
        self.assertTrue(L('ABC').isalnum())
        self.assertTrue(L('123').isalnum())
        
    def test_isalnum_mixed(self):
        """Символы с пробелами или спецсимволами возвращают False."""
        self.assertFalse(L('abc 123').isalnum())
        self.assertFalse(L('abc-123').isalnum())
        self.assertFalse(L('').isalnum())
        
    def test_isupper_uppercase(self):
        """Строки только в верхнем регистре возвращают True."""
        self.assertTrue(L('ABC').isupper())
        self.assertTrue(L('ABC123').isupper())  # Цифры не учитываются
        
    def test_isupper_mixed_case(self):
        """Смешанный регистр возвращает False."""
        self.assertFalse(L('Abc').isupper())
        self.assertFalse(L('abc').isupper())
        
    def test_isupper_no_cased(self):
        """Строки без букв возвращают False."""
        self.assertFalse(L('123').isupper())
        self.assertFalse(L('').isupper())
        
    def test_islower_lowercase(self):
        """Строки только в нижнем регистре возвращают True."""
        self.assertTrue(L('abc').islower())
        self.assertTrue(L('abc123').islower())  # Цифры не учитываются
        
    def test_islower_mixed_case(self):
        """Смешанный регистр возвращает False."""
        self.assertFalse(L('Abc').islower())
        self.assertFalse(L('ABC').islower())
        
    def test_islower_no_cased(self):
        """Строки без букв возвращают False."""
        self.assertFalse(L('123').islower())
        self.assertFalse(L('').islower())
        
    def test_isdecimal_decimal_digits(self):
        """Десятичные цифры возвращают True."""
        self.assertTrue(L('123').isdecimal())
        self.assertTrue(L('0').isdecimal())
        
    def test_isdecimal_mixed(self):
        """Не только цифры возвращают False."""
        self.assertFalse(L('12a').isdecimal())
        self.assertFalse(L('').isdecimal())
        
    def test_isnumeric_numeric(self):
        """Числовые символы возвращают True."""
        self.assertTrue(L('123').isnumeric())
        self.assertTrue(L('½').isnumeric())  # Дробь
        self.assertTrue(L('⅓').isnumeric())  # Другая дробь
        
    def test_isnumeric_non_numeric(self):
        """Нечисловые символы возвращают False."""
        self.assertFalse(L('abc').isnumeric())
        self.assertFalse(L('').isnumeric())
        
    def test_isprintable_printable(self):
        """Печатные символы возвращают True."""
        self.assertTrue(L('abc 123').isprintable())
        self.assertTrue(L('ABC!@#').isprintable())
        
    def test_isprintable_non_printable(self):
        """Непечатные символы возвращают False."""
        self.assertFalse(L('abc\n123').isprintable())
        self.assertFalse(L('\t').isprintable())
        
    def test_isprintable_empty(self):
        """Пустая строка считается печатной."""
        self.assertTrue(L('').isprintable())
        
    def test_istitle_titlecase(self):
        """Строки в заглавном регистре возвращают True."""
        self.assertTrue(L('Hello World').istitle())
        self.assertTrue(L('Hello').istitle())
        
    def test_istitle_not_titlecase(self):
        """Строки не в заглавном регистре возвращают False."""
        self.assertFalse(L('Hello world').istitle())
        self.assertFalse(L('HELLO WORLD').istitle())
        self.assertFalse(L('hello world').istitle())
        self.assertFalse(L('').istitle())


class TestLStrCharacterClassesBufferTypes(unittest.TestCase):
    """Тесты для методов определения классов символов с разными типами буферов."""
    
    def test_joinbuffer_isupper(self):
        """JoinBuffer корректно определяет верхний регистр."""
        result = L('AB') + L('C')
        self.assertTrue(result.isupper())
        
        result = L('AB') + L('c')
        self.assertFalse(result.isupper())
        
    def test_mulbuffer_isdigit(self):
        """MulBuffer корректно определяет цифры."""
        result = L('1') * 3
        self.assertTrue(result.isdigit())
        
        result = L('a') * 3
        self.assertFalse(result.isdigit())
        
    def test_slicebuffer_isupper(self):
        """SliceBuffer корректно определяет верхний регистр."""
        result = L('xABCx')[1:4]
        self.assertTrue(result.isupper())
        
        result = L('xAbCx')[1:4]
        self.assertFalse(result.isupper())
        
    def test_slicebuffer_step_isdigit(self):
        """SliceBuffer с шагом корректно определяет цифры."""
        result = L('1a2b3c')[::2]  # '123'
        self.assertTrue(result.isdigit())
        
        result = L('a1b2c3')[::2]  # 'abc'
        self.assertFalse(result.isdigit())
        
    def test_complex_buffer_isalpha(self):
        """Сложные операции с буферами."""
        result = (L('ab') + L('cd')) * 2  # 'abcdabcd'
        self.assertTrue(result.isalpha())
        
        result = (L('a') + L('1')) * 2  # 'a1a1'
        self.assertFalse(result.isalpha())


class TestLStrCharacterClassesVsStr(unittest.TestCase):
    """Тесты для сравнения поведения L и str."""
    
    def test_isspace_match_str(self):
        """isspace() должен давать тот же результат, что и str."""
        test_cases = [' \t\n', 'abc', '', '  ', ' a ']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isspace(), s.isspace())
                
    def test_isalpha_match_str(self):
        """isalpha() должен давать тот же результат, что и str."""
        test_cases = ['abc', 'ABC', 'abc123', '', 'a b']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isalpha(), s.isalpha())
                
    def test_isdigit_match_str(self):
        """isdigit() должен давать тот же результат, что и str."""
        test_cases = ['123', '0', '12a', '', '1 2']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isdigit(), s.isdigit())
                
    def test_isalnum_match_str(self):
        """isalnum() должен давать тот же результат, что и str."""
        test_cases = ['abc123', 'ABC', '123', '', 'abc 123']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isalnum(), s.isalnum())
                
    def test_isupper_match_str(self):
        """isupper() должен давать тот же результат, что и str."""
        test_cases = ['ABC', 'ABC123', 'Abc', 'abc', '123', '']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isupper(), s.isupper())
                
    def test_islower_match_str(self):
        """islower() должен давать тот же результат, что и str."""
        test_cases = ['abc', 'abc123', 'Abc', 'ABC', '123', '']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).islower(), s.islower())
                
    def test_isdecimal_match_str(self):
        """isdecimal() должен давать тот же результат, что и str."""
        test_cases = ['123', '0', '12a', '']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isdecimal(), s.isdecimal())
                
    def test_isnumeric_match_str(self):
        """isnumeric() должен давать тот же результат, что и str."""
        test_cases = ['123', '½', 'abc', '']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isnumeric(), s.isnumeric())
                
    def test_isprintable_match_str(self):
        """isprintable() должен давать тот же результат, что и str."""
        test_cases = ['abc 123', 'ABC!@#', 'abc\n123', '\t', '']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).isprintable(), s.isprintable())
                
    def test_istitle_match_str(self):
        """istitle() должен давать тот же результат, что и str."""
        test_cases = ['Hello World', 'Hello', 'Hello world', 'HELLO WORLD', 'hello world', '']
        for s in test_cases:
            with self.subTest(s=s):
                self.assertEqual(L(s).istitle(), s.istitle())


if __name__ == '__main__':
    unittest.main()
