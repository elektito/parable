import parable
from parable import Symbol

import unittest

class SymbolTest(unittest.TestCase):
    def test_equal(self):
        self.assertEqual(Symbol('foo'), Symbol('foo'))

    def test_not_equal(self):
        self.assertNotEqual(Symbol('foo'), Symbol('bar'))

    def test_hash(self):
        d = {}
        d[Symbol('foo')] = 1000
        d[Symbol('foo')] = 2000
        d[Symbol('bar')] = 3000

        self.assertEqual(d[Symbol('foo')], 2000)
        self.assertEqual(d[Symbol('bar')], 3000)

class ParableCoreTest(unittest.TestCase):
    def eval_str(self, s):
        exp = parable.parse_str(s)
        return parable.eval(exp, {})

    def test_shorthand_quote(self):
        exp = "'x"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = "(first '(x y))"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('x'))

        # quote character as a separator (no space before the second
        # quote).
        exp = "('x'y)"
        result = parable.read_str(exp)
        self.assertEqual(result, [[Symbol('quote'), Symbol('x')], [Symbol('quote'), Symbol('y')]])

    def test_integer(self):
        exp = '1080'
        result = self.eval_str(exp)
        self.assertEqual(result, 1080)

    def test_string(self):
        exp = '"foobar"'
        result = self.eval_str(exp)
        self.assertEqual(result, 'foobar')

    def test_if(self):
        exp = "(if 't 'a 'b)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('a'))

        exp = "(if '() 'a 'b)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('b'))

    def test_quote(self):
        exp = '(quote x)'
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('x'))

    def test_atom(self):
        exp = "(atom 'x)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('t'))

        exp = "(atom '(x y))"
        result = self.eval_str(exp)
        self.assertEqual(result, [])

    def test_first(self):
        exp = "(first '(x y z))"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('x'))

    def test_rest(self):
        exp = "(rest '(x y z))"
        result = self.eval_str(exp)
        self.assertEqual(result, [Symbol('y'), Symbol('z')])

    def test_prep(self):
        exp = "(prep 'x '(y z))"
        result = self.eval_str(exp)
        self.assertEqual(result, [Symbol(i) for i in ['x', 'y', 'z']])

    def test_eq(self):
        exp = "(eq 'x 'x)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('t'))

        exp = "(eq 'x 'y)"
        result = self.eval_str(exp)
        self.assertEqual(result, [])

        exp = "(eq '(a b) '(a b))"
        result = self.eval_str(exp)
        self.assertEqual(result, [])

    def test_function_call(self):
        exp = "((fn (a b c) b) 'a 'b 'c)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('b'))

    def test_function_call_with_rest(self):
        exp = "((fn (a b &rest r) (prep a (prep b r))) 'a 'b 'c 'd)"
        result = self.eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('d')])

        # test sending nothing for &rest
        exp = "((fn (a b &rest r) (prep a (prep b r))) 'a 'b)"
        result = self.eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b')])

    def test_macro_call(self):
        exp = "((mac (a b c) b) (a b) (if 't 'a 'b) (p q))"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('a'))

    def test_macro_call_with_rest(self):
        exp = "((mac (a (b c &rest d) e &rest f) d) a (b c quote dR1) e quote dR2)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('dR1'))

        exp = "((mac (a (b c &rest d) e &rest f) f) a (b c quote dR1) e quote dR2)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('dR2'))

    def test_destructuring_macro_call(self):
        exp = "((mac (a (b (c)) d) (prep a (prep b (prep c (prep d '()))))) if ('t ('a)) 'b)"
        result = self.eval_str(exp)
        self.assertEqual(result, Symbol('a'))

if __name__ == '__main__':
    unittest.main()
