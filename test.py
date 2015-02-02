import parable
from parable import Symbol

import unittest

class SymbolTest(unittest.TestCase):
    def test_equal(self):
        self.assertTrue(Symbol('foo') == Symbol('foo'))
        self.assertFalse(Symbol('foo') == Symbol('bar'))

    def test_not_equal(self):
        self.assertFalse(Symbol('foo') != Symbol('foo'))
        self.assertTrue(Symbol('foo') != Symbol('bar'))

    def test_hash(self):
        d = {}
        d[Symbol('foo')] = 1000
        d[Symbol('foo')] = 2000
        d[Symbol('bar')] = 3000

        self.assertEqual(d[Symbol('foo')], 2000)
        self.assertEqual(d[Symbol('bar')], 3000)

def eval_str(s):
    exp = parable.read_str(s)
    return parable.eval(exp, {})

class ParableCoreTest(unittest.TestCase):
    def test_empty(self):
        exp = ''
        result = parable.read_str(exp)
        self.assertEqual(result, None)

        exp = '\n\n\n\n\t    \n\n'
        result = parable.read_str(exp)
        self.assertEqual(result, None)

    def test_whitespace(self):
        exp = '   x'
        result = parable.read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = '\n\nx\n\n\n\n'
        result = parable.read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = '(\na\tb c\nd\re  \n)'
        result = parable.read_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('d'), Symbol('e')])

    def test_comments(self):
        exp = "x ;foobar"
        result = parable.read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = "(x;comment as a separator\ny)"
        result = parable.read_str(exp)
        self.assertEqual(result, [Symbol('x'), Symbol('y')])

        exp = "x;comment as separator"
        result = parable.read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = ";beginning comments\n(x ;foobar\ny); end comments\n"
        result = parable.read_str(exp)
        self.assertEqual(result, [Symbol('x'), Symbol('y')])

    def test_shorthand_quote(self):
        exp = "'x"
        result = parable.read_str(exp)
        self.assertEqual(result, [Symbol('quote'), Symbol('x')])

        exp = "'   x"
        result = parable.read_str(exp)
        self.assertEqual(result, [Symbol('quote'), Symbol('x')])

        exp = "'(x y)"
        result = parable.read_str(exp)
        self.assertEqual(result, [Symbol('quote'), [Symbol('x'), Symbol('y')]])

        # quote character as a separator (no space before the second
        # quote).
        exp = "('x'y)"
        result = parable.read_str(exp)
        self.assertEqual(result, [[Symbol('quote'), Symbol('x')], [Symbol('quote'), Symbol('y')]])

    def test_integer(self):
        exp = '1080'
        result = eval_str(exp)
        self.assertEqual(result, 1080)

    def test_string(self):
        exp = '"foobar"'
        result = eval_str(exp)
        self.assertEqual(result, 'foobar')

    def test_if(self):
        exp = "(if 't 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('a'))

        exp = "(if '() 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('b'))

    def test_quote(self):
        exp = '(quote x)'
        result = eval_str(exp)
        self.assertEqual(result, Symbol('x'))

    def test_atom(self):
        exp = "(atom 'x)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('t'))

        exp = "(atom '(x y))"
        result = eval_str(exp)
        self.assertEqual(result, [])

    def test_first(self):
        exp = "(first '(x y z))"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('x'))

    def test_rest(self):
        exp = "(rest '(x y z))"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('y'), Symbol('z')])

    def test_prep(self):
        exp = "(prep 'x '(y z))"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol(i) for i in ['x', 'y', 'z']])

    def test_eq(self):
        exp = "(eq 'x 'x)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('t'))

        exp = "(eq 'x 'y)"
        result = eval_str(exp)
        self.assertEqual(result, [])

        exp = "(eq '(a b) '(a b))"
        result = eval_str(exp)
        self.assertEqual(result, [])

    def test_function_call(self):
        exp = "((fn (a b c) b) 'a 'b 'c)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('b'))

    def test_function_call_with_rest(self):
        exp = "((fn (a b &rest r) (prep a (prep b r))) 'a 'b 'c 'd)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('d')])

        # test sending nothing for &rest
        exp = "((fn (a b &rest r) (prep a (prep b r))) 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b')])

    def test_macro_call(self):
        exp = "((mac (a b c) b) (a b) (if 't 'a 'b) (p q))"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('a'))

    def test_macro_call_with_rest(self):
        exp = "((mac (a (b c &rest d) e &rest f) d) a (b c quote dR1) e quote dR2)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('dR1'))

        exp = "((mac (a (b c &rest d) e &rest f) f) a (b c quote dR1) e quote dR2)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('dR2'))

    def test_destructuring_macro_call(self):
        exp = "((mac (a (b (c)) d) (prep a (prep b (prep c (prep d '()))))) if ('t ('a)) 'b)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('a'))

class ParableUtilsTest(unittest.TestCase):
    def test_macro_expand_single(self):
        exp = "((mac (a) 'a) 'x))"
        exp = parable.read_str(exp)

        result, expanded = parable.macro_expand_1(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, Symbol('a'))

        result, expanded = parable.macro_expand(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, Symbol('a'))

    def test_macro_expand_multi(self):
        exp = "((mac (a) '((mac () 1000))) 'x))"
        exp = parable.read_str(exp)

        result, expanded = parable.macro_expand_1(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, [[Symbol('mac'), [], 1000]])

        result, expanded = parable.macro_expand(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, 1000)

    def test_macro_expand_none(self):
        exp = "x"
        exp = parable.read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, Symbol('x'))
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, Symbol('x'))

        exp = "()"
        exp = parable.read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [])
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [])

        exp = "(car x)"
        exp = parable.read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [Symbol('car'), Symbol('x')])
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [Symbol('car'), Symbol('x')])

        exp = "1000"
        exp = parable.read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, 1000)
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, 1000)

if __name__ == '__main__':
    unittest.main()
