import parable
from parable import Symbol, Function, Macro, List, Integer, String, EvalError
from read import Reader
from pprint import pprint

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

class ListTest(unittest.TestCase):
    def setUp(self):
        self.list = List([1, 2, 3, 4, 5])

    def test_equality(self):
        self.assertEqual(self.list, [1, 2, 3, 4, 5])

    def test_get_item(self):
        self.assertEqual(self.list[0], 1)
        self.assertEqual(self.list[4], 5)
        self.assertEqual(self.list[-1], 5)

        with self.assertRaises(IndexError):
            self.list[5]

    def test_set_item(self):
        self.list[0] = 10
        self.assertEqual(self.list[0], 10)

        self.list[-1] = 50
        self.assertEqual(self.list[-1], 50)

    def test_get_slice(self):
        self.assertEqual(self.list[1:3], [2, 3])
        self.assertEqual(type(self.list[1:3]), List)
        self.assertEqual(self.list[1:3:2], [2])
        self.assertEqual(type(self.list[1:3:2]), List)
        self.assertEqual(self.list[5:], [])
        self.assertEqual(type(self.list[5:]), List)

class IntegerTest(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(Integer(1), Integer(1))
        self.assertEqual(Integer(1), 1)
        self.assertEqual(Integer(-1), -1)

    def test_addition(self):
        self.assertEqual(Integer(1) + 1, Integer(2))
        self.assertEqual(1 + Integer(1), Integer(2))
        self.assertEqual(Integer(1) + Integer(1), Integer(2))

class StringTest(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(String('foo'), String('foo'))
        self.assertEqual(String('foo'), 'foo')
        self.assertEqual(String(), '')

    def test_addition(self):
        self.assertEqual(String('foo') + 'bar', String('foobar'))
        self.assertTrue(isinstance(String('foo') + 'bar', String))
        self.assertEqual('foo' + String('bar'), String('foobar'))
        self.assertTrue(isinstance('foo' + String('bar'), String))
        self.assertEqual(String('foo') + String('bar'), String('foobar'))
        self.assertTrue(isinstance(String('foo') + String('bar'), String))

def read_str(s):
    return Reader(s, '<string>').read()

class ReaderTest(unittest.TestCase):
    def test_empty(self):
        exp = ''
        result = read_str(exp)
        self.assertEqual(result, None)

        exp = '\n\n\n\n\t    \n\n'
        result = read_str(exp)
        self.assertEqual(result, None)

    def test_whitespace(self):
        exp = '   x'
        result = read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = '\n\nx\n\n\n\n'
        result = read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = '(\na\tb c\nd e  \n)'
        result = read_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('d'), Symbol('e')])

    def test_comments(self):
        exp = "x ;foobar"
        result = read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = "(x;comment as a separator\ny)"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('x'), Symbol('y')])

        exp = "x;comment as separator"
        result = read_str(exp)
        self.assertEqual(result, Symbol('x'))

        exp = ";beginning comments\n(x ;foobar\ny); end comments\n"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('x'), Symbol('y')])

        exp = '"x;not-a-comment"'
        result = read_str(exp)
        self.assertEqual(result, "x;not-a-comment")

    def test_shorthand_quote(self):
        exp = "'x"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('quote'), Symbol('x')])

        exp = "'   x"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('quote'), Symbol('x')])

        exp = "'(x y)"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('quote'), [Symbol('x'), Symbol('y')]])

        # quote character as a separator (no space before the second
        # quote).
        exp = "('x'y)"
        result = read_str(exp)
        self.assertEqual(result, [[Symbol('quote'), Symbol('x')], [Symbol('quote'), Symbol('y')]])

    def test_shorthand_backquote(self):
        exp = '`x'
        result = read_str(exp)
        self.assertEqual(result, [Symbol('backquote'), Symbol('x')])

    def test_shorthand_unquote(self):
        exp = ',x'
        result = read_str(exp)
        self.assertEqual(result, [Symbol('unquote'), Symbol('x')])

    def test_shorthand_unquote_splicing(self):
        exp = ',@x'
        result = read_str(exp)
        self.assertEqual(result, [Symbol('unquote-splicing'), Symbol('x')])

    def test_integer(self):
        exp = '1080'
        result = read_str(exp)
        self.assertEqual(result, 1080)

    def test_string(self):
        exp = '"foobar"'
        result = read_str(exp)
        self.assertEqual(result, 'foobar')

    def test_nil(self):
        exp = "()"
        result = read_str(exp)
        self.assertEqual(result, [])

    def test_list(self):
        exp = "(1 2 x)"
        result = read_str(exp)
        self.assertEqual(result, [1, 2, Symbol('x')])

        exp = "(eq 'x 'x)"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('eq'),
                                  [Symbol('quote'), Symbol('x')],
                                  [Symbol('quote'), Symbol('x')]])

    def test_nested_list(self):
        exp = "(1 (2 foo) x)"
        result = read_str(exp)
        self.assertEqual(result, [1, [2, Symbol('foo')], Symbol('x')])

        exp = "(eq (a b) (a b))"
        result = read_str(exp)
        self.assertEqual(result, [Symbol('eq'),
                                  [Symbol('a'), Symbol('b')],
                                  [Symbol('a'), Symbol('b')]])

    def test_multi(self):
        exp = '"foo"(1 2 x)1(a b)'
        reader = Reader(exp, '<string>')

        result = reader.read()
        self.assertEqual(result, 'foo')

        result = reader.read()
        self.assertEqual(result, [1, 2, Symbol('x')])

        result = reader.read()
        self.assertEqual(result, 1)

        result = reader.read()
        self.assertEqual(result, [Symbol('a'), Symbol('b')])

    def test_position(self):
        exp = '(100 foo "bar")'
        result = read_str(exp)

        self.assertEqual(result.start_row, 0)
        self.assertEqual(result.start_col, 0)
        self.assertEqual(result.end_row, 0)
        self.assertEqual(result.end_col, 14)

        self.assertEqual(result[0].start_row, 0)
        self.assertEqual(result[0].start_col, 1)
        self.assertEqual(result[0].end_row, 0)
        self.assertEqual(result[0].end_col, 3)

        self.assertEqual(result[1].start_row, 0)
        self.assertEqual(result[1].start_col, 5)
        self.assertEqual(result[1].end_row, 0)
        self.assertEqual(result[1].end_col, 7)

        self.assertEqual(result[2].start_row, 0)
        self.assertEqual(result[2].start_col, 9)
        self.assertEqual(result[2].end_row, 0)
        self.assertEqual(result[2].end_col, 13)

def eval_str(s, env={}):
    exp = read_str(s)
    return parable.eval(exp, env)

class ParableCoreTest(unittest.TestCase):
    def test_integer(self):
        exp = '1080'
        result = eval_str(exp)
        self.assertEqual(result, 1080)

    def test_string(self):
        exp = '"foobar"'
        result = eval_str(exp)
        self.assertEqual(result, 'foobar')

    def test_nil(self):
        exp = "nil"
        result = eval_str(exp)
        self.assertEqual(result, [])

        exp = "'()"
        result = eval_str(exp)
        self.assertEqual(result, [])

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

    def test_typeof(self):
        exp = "(typeof 'x)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('symbol'))

        exp = "(typeof 10)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('int'))

        exp = '(typeof "foo")'
        result = eval_str(exp)
        self.assertEqual(result, Symbol('str'))

        exp = "(typeof '(x y))"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('list'))

        exp = "(typeof (fn (x) 100))"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('function'))

        exp = "(typeof (mac (x) x))"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('macro'))

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

        exp = "(eq 1 1)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('t'))

        exp = "(eq 1 2)"
        result = eval_str(exp)
        self.assertEqual(result, [])

        exp = '(eq "foo" "foo")'
        result = eval_str(exp)
        self.assertEqual(result, Symbol('t'))

        exp = '(eq "foo" "fooo")'
        result = eval_str(exp)
        self.assertEqual(result, [])

        exp = '(eq 1 "1")'
        result = eval_str(exp)
        self.assertEqual(result, [])

        # This was not originally planned, after all two lists are not
        # `eq` and we weren't supposed to treat the empty list
        # specially. However, as long as nil is used for `false` we
        # need it to be equal to itself. Perhaps we'd better use
        # separate true and false values like in clojure?
        exp = '(eq nil nil)'
        result = eval_str(exp)
        self.assertEqual(result, Symbol('t'))

    def test_apply(self):
        exp = "(apply (fn (x y) (prep y (prep x '()))) '(10 20))"
        result = eval_str(exp)
        self.assertEqual(result, [20, 10])

        exp = "(apply (fn () 10) '())"
        result = eval_str(exp)
        self.assertEqual(result, 10)

        exp = "(apply (fn (x) x) '((1)))"
        result = eval_str(exp)
        self.assertEqual(result, [1])

    def test_function_call(self):
        exp = "((fn (a b c) b) 'a 'b 'c)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('b'))

    def test_nested_function_call(self):
        list_func = '(fn (&rest r) r)'
        list_func = eval_str(list_func)
        env = {Symbol('list'): list_func}
        exp = "(list 1 (list 100 200) 2)"
        result = eval_str(exp, env)
        self.assertEqual(result, [1, [100, 200], 2])

    def test_function_call_with_rest(self):
        exp = "((fn (a b &rest r) (prep a (prep b r))) 'a 'b 'c 'd)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('d')])

        # test sending nothing for &rest
        exp = "((fn (a b &rest r) (prep a (prep b r))) 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b')])

    def test_too_many_arguments_to_function(self):
        exp = "((fn (x) x) 1 2)"
        with self.assertRaises(EvalError):
            result = eval_str(exp)

    def test_too_few_arguments_to_function(self):
        exp = "((fn (x y) x) 1)"
        with self.assertRaises(EvalError):
            result = eval_str(exp)

    def test_too_few_arguments_to_function_with_rest(self):
        exp = "((fn (x &rest y) x))"
        with self.assertRaises(EvalError):
            result = eval_str(exp)

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

    def test_too_many_arguments_to_macro(self):
        exp = "((mac (x) x) 1 2)"
        with self.assertRaises(EvalError):
            result = eval_str(exp)

    def test_too_few_arguments_to_macro(self):
        exp = "((mac (x y) x) 1)"
        with self.assertRaises(EvalError):
            result = eval_str(exp)

    def test_too_few_arguments_to_macro_with_rest(self):
        exp = "((mac (x &rest y) x))"
        with self.assertRaises(EvalError):
            result = eval_str(exp)

    def test_lexical_scope(self):
        # first create a function that returns the value of a symbol x
        # in its lexical scope, with x = 10.
        exp = "((fn (x) (fn () x)) 10)"
        func = eval_str(exp)
        self.assertTrue(isinstance(func, Function))

        # now call the function in an environment where x is 20 and
        # make sure it still returns 10.
        exp = "(foo)"
        result = eval_str(exp, {Symbol('x'): 20, Symbol('foo'): func})
        self.assertEqual(result, 10)

class ParableUtilsTest(unittest.TestCase):
    def test_macro_expand_single(self):
        exp = "((mac (a) 'a) 'x))"
        exp = read_str(exp)

        result, expanded = parable.macro_expand_1(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, Symbol('a'))

        result, expanded = parable.macro_expand(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, Symbol('a'))

    def test_macro_expand_multi(self):
        exp = "((mac (a) '((mac () 1000))) 'x))"
        exp = read_str(exp)

        result, expanded = parable.macro_expand_1(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, [[Symbol('mac'), [], 1000]])

        result, expanded = parable.macro_expand(exp, {})
        self.assertTrue(expanded)
        self.assertEqual(result, 1000)

    def test_macro_expand_none(self):
        exp = "x"
        exp = read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, Symbol('x'))
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, Symbol('x'))

        exp = "()"
        exp = read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [])
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [])

        exp = "(car x)"
        exp = read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [Symbol('car'), Symbol('x')])
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, [Symbol('car'), Symbol('x')])

        exp = "1000"
        exp = read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, 1000)
        result, expanded = parable.macro_expand(exp, {})
        self.assertFalse(expanded)
        self.assertEqual(result, 1000)

    def test_pprint(self):
        self.assertEqual(pprint([]), 'nil')
        self.assertEqual(pprint(Symbol('foo')), 'foo')
        self.assertEqual(pprint(String("foo")), '"foo"')
        self.assertEqual(pprint(Integer(1018)), '1018')
        self.assertEqual(pprint([Symbol('quote'), Symbol('foo')]), "'foo")
        self.assertEqual(pprint([Symbol('backquote'), Symbol('x')]), '`x')
        self.assertEqual(pprint([Symbol('unquote'), Symbol('x')]), ',x')
        self.assertEqual(pprint([Symbol('unquote-splicing'), Symbol('x')]), ',@x')
        self.assertEqual(pprint(Function(List(), 10, {})), '(fn () 10)')
        self.assertEqual(pprint(Function(List([Symbol('x')]), 10, {})), '(fn (x) 10)')
        self.assertEqual(pprint(Macro(List([Symbol('x')]), 10, {})), '(mac (x) 10)')

if __name__ == '__main__':
    unittest.main()
