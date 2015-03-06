import parable
from parable import Error, Symbol, Function, Macro, List, Bool, Integer, String, create_error
from read import Reader, ReadError, EofReadError
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

        exp = '\n\n\n   x'
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

    def test_bool(self):
        exp = '#t'
        result = read_str(exp)
        self.assertEqual(result, Bool(True))

        exp = '#f'
        result = read_str(exp)
        self.assertEqual(result, Bool(False))

    def test_integer(self):
        exp = '1080'
        result = read_str(exp)
        self.assertEqual(result, 1080)

    def test_string(self):
        exp = '"foobar"'
        result = read_str(exp)
        self.assertEqual(result, 'foobar')

        exp = '"foo\\bar"'
        result = read_str(exp)
        self.assertEqual(result, 'foobar')

        exp = '"sth \\"sth\\" sth"'
        result = read_str(exp)
        self.assertEqual(result, 'sth "sth" sth')

        exp = '"\\"foo"'
        result = read_str(exp)
        self.assertEqual(result, '"foo')

        exp = '"\\""'
        result = read_str(exp)
        self.assertEqual(result, '"')

        with self.assertRaises(ReadError):
            exp = '"foo\\'
            result = read_str(exp)

        with self.assertRaises(ReadError):
            exp = '"foo\\"'
            result = read_str(exp)

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

    def test_unexpected_end_of_file_in_list(self):
        with self.assertRaises(EofReadError):
            exp = '(100 foo "bar"'
            result = read_str(exp)

    def test_unexpected_end_of_file_in_string(self):
        with self.assertRaises(EofReadError):
            exp = '"bar'
            result = read_str(exp)

def eval_str(s, env={}):
    exp = read_str(s)
    return parable.eval(exp, env)

class ParableCoreTest(unittest.TestCase):
    def test_bool(self):
        exp = '#t'
        result = eval_str(exp)
        self.assertEqual(result, Bool(True))

        exp = '#f'
        result = eval_str(exp)
        self.assertEqual(result, Bool(False))

        exp = "'(#t #f)"
        result = eval_str(exp)
        self.assertEqual(result, [Bool(True), Bool(False)])

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

    def test_keyword(self):
        exp = ":foo"
        result = eval_str(exp)
        self.assertEqual(result, Symbol(':foo'))

    def test_error(self):
        exp = '(error :foo)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

        exp = '(error :foo 1 :sym "foo")'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

        exp = '(error "foo")'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':error-error'))

        exp = '(error)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':error-error'))

    def test_error_arg_evaluation(self):
        exp = "(error (first '(:foo :bar)) :msg (first '(\"foo\" \"bar\")))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))
        self.assertEqual(result.attrs, [Symbol(':msg'), "foo"])

    def test_error_type(self):
        exp = '(error-type (error :foo))'
        result = eval_str(exp)
        self.assertEqual(result, Symbol(':foo'))

    def test_error_type(self):
        exp = '(error-attrs (error :foo :a 10 :b 20))'
        result = eval_str(exp)
        self.assertEqual(result, List([Symbol(':a'), Integer(10), Symbol(':b'), Integer(20)]))

    def test_if(self):
        exp = "(if #t 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('a'))

        exp = "(if #f 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('b'))

        exp = "(if nil 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

    def test_quote(self):
        exp = '(quote x)'
        result = eval_str(exp)
        self.assertEqual(result, Symbol('x'))

    def test_typeof(self):
        exp = "(typeof 'x)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('symbol'))

        exp = "(typeof #t)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('bool'))

        exp = "(typeof #f)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('bool'))

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
        self.assertEqual(result, True)

        exp = "(eq 'x 'y)"
        result = eval_str(exp)
        self.assertEqual(result, False)

        exp = "(eq '(a b) '(a b))"
        result = eval_str(exp)
        self.assertEqual(result, False)

        exp = "(eq 1 1)"
        result = eval_str(exp)
        self.assertEqual(result, True)

        exp = "(eq 1 2)"
        result = eval_str(exp)
        self.assertEqual(result, False)

        exp = '(eq "foo" "foo")'
        result = eval_str(exp)
        self.assertEqual(result, True)

        exp = '(eq "foo" "fooo")'
        result = eval_str(exp)
        self.assertEqual(result, False)

        exp = '(eq 1 "1")'
        result = eval_str(exp)
        self.assertEqual(result, False)

        # This was not originally planned, after all two lists are not
        # `eq` and we weren't supposed to treat the empty list
        # specially. However, as long as nil is used for `false` we
        # need it to be equal to itself. Perhaps we'd better use
        # separate true and false values like in clojure?
        exp = '(eq nil nil)'
        result = eval_str(exp)
        self.assertEqual(result, True)

    def test_fn(self):
        exp = '(fn)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':form-error'))

        exp = '(fn ())'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':form-error'))

    def test_mac(self):
        exp = '(mac)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':form-error'))

        exp = '(mac ())'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':form-error'))

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

    def test_duplicate_function_parameter_list(self):
        exp = '(fn (x x) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(fn (x y x) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(fn (x y & y) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_duplicate_macro_parameter_list(self):
        exp = '(mac (x x) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac (x y x) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac (x y & y) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac (x (y z) & y) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac (x (y y) z) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac (x (a (y y) b) z) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_non_list_function_parameter_list(self):
        exp = '(fn 1 x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(fn x x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(fn "()" x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_non_list_macro_parameter_list(self):
        exp = '(mac 1 x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac x x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac "()" x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_invalid_function_rest_paramter(self):
        exp = '(fn (x & y z) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_more_than_one_rest_parameter_in_function(self):
        exp = '(fn (x & y & z) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_invalid_macro_rest_paramter(self):
        exp = '(mac (x & y z) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_more_than_one_rest_parameter_in_macro(self):
        exp = '(mac (x & y & z) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

        exp = '(mac (x (h & y & z) g) x)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':param-error'))

    def test_nested_function_call(self):
        list_func = '(fn (& r) r)'
        list_func = eval_str(list_func)
        env = {Symbol('list'): list_func}
        exp = "(list 1 (list 100 200) 2)"
        result = eval_str(exp, env)
        self.assertEqual(result, [1, [100, 200], 2])

    def test_function_call_with_rest(self):
        exp = "((fn (a b & r) (prep a (prep b r))) 'a 'b 'c 'd)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b'), Symbol('c'), Symbol('d')])

        # test sending nothing for the rest argument
        exp = "((fn (a b & r) (prep a (prep b r))) 'a 'b)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('a'), Symbol('b')])

    def test_too_many_arguments_to_function(self):
        exp = "((fn (x) x) 1 2)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_too_few_arguments_to_function(self):
        exp = "((fn (x y) x) 1)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_too_few_arguments_to_function_with_rest(self):
        exp = "((fn (x & y) x))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_macro_call(self):
        exp = "((mac (a b c) b) (a b) (if #t 'a 'b) (p q))"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('a'))

    def test_macro_call_with_rest(self):
        exp = "((mac (a (b c & d) e & f) d) a (b c quote dR1) e quote dR2)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('dR1'))

        exp = "((mac (a (b c & d) e & f) f) a (b c quote dR1) e quote dR2)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('dR2'))

    def test_destructuring_macro_call(self):
        exp = "((mac (a (b (c)) d) (prep a (prep b (prep c (prep d '()))))) if (#t ('a)) 'b)"
        result = eval_str(exp)
        self.assertEqual(result, Symbol('a'))

    def test_too_many_arguments_to_macro(self):
        exp = "((mac (x) x) 1 2)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_too_few_arguments_to_macro(self):
        exp = "((mac (x y) x) 1)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_too_few_arguments_to_macro_with_rest(self):
        exp = "((mac (x & y) x))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

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

    def test_macro_expand_arg_error(self):
        exp = "((mac () x) 10)"
        exp = read_str(exp)
        result, expanded = parable.macro_expand_1(exp, {})
        self.assertEqual(result, create_error(':arg-error'))
        self.assertEqual(expanded, False)

class PrettyPrintTest(unittest.TestCase):
    def test_pprint_nil(self):
        self.assertEqual(pprint([]), 'nil')

    def test_pprint_symbol(self):
        self.assertEqual(pprint(Symbol('foo')), 'foo')

    def test_pprint_string(self):
        self.assertEqual(pprint(String("foo")), '"foo"')
        self.assertEqual(pprint(String('sth "sth" sth')), '"sth \\"sth\\" sth"')

    def test_pprint_boolean(self):
        self.assertEqual(pprint(True), '#t')
        self.assertEqual(pprint(False), '#f')

    def test_pprint_integer(self):
        self.assertEqual(pprint(Integer(1018)), '1018')

    def test_pprint_quote(self):
        self.assertEqual(pprint([Symbol('quote'), Symbol('foo')]), "'foo")

    def test_pprint_backquote(self):
        self.assertEqual(pprint([Symbol('backquote'), Symbol('x')]), '`x')

    def test_pprint_unquote(self):
        self.assertEqual(pprint([Symbol('unquote'), Symbol('x')]), ',x')

    def test_pprint_unquote_splicing(self):
        self.assertEqual(pprint([Symbol('unquote-splicing'), Symbol('x')]), ',@x')

    def test_pprint_function(self):
        self.assertEqual(pprint(Function(List(), 10, {})), '(fn () 10)')
        self.assertEqual(pprint(Function(List([Symbol('x')]), 10, {})), '(fn (x) 10)')

    def test_pprint_macro(self):
        self.assertEqual(pprint(Macro(List(), 10, {})), '(mac () 10)')
        self.assertEqual(pprint(Macro(List([Symbol('x')]), 10, {})), '(mac (x) 10)')

    def test_pprint_error(self):
        self.assertEqual(pprint(create_error(':foo')), '(error :foo)')
        self.assertEqual(pprint(create_error(':foo', ':a', 10)), '(error :foo :a 10)')

class ErrorTest(unittest.TestCase):
    def test_create_error(self):
        err = create_error(':foo', ':a', 10, ':b', 20)
        self.assertEqual(err, Error(Symbol(':foo'), []))
        self.assertEqual(err.attrs, [Symbol(':a'), 10, Symbol(':b'), 20])

        with self.assertRaises(RuntimeError):
            err = create_error(':foo', 10)

        with self.assertRaises(RuntimeError):
            err = create_error(10)

    def test_good_quote(self):
        exp = "'(error :foo)"
        result = eval_str(exp)
        self.assertEqual(result, [Symbol('error'), Symbol(':foo')])

    def test_bad_quote(self):
        exp = "(quote x y)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(quote)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_good_eq(self):
        exp = '(eq (error :foo) :bar)'
        result = eval_str(exp)
        self.assertEqual(result, Bool(False))

        exp = '(eq (error :foo) (error :foo))'
        result = eval_str(exp)
        self.assertEqual(result, Bool(True))

        exp = '(eq (error :foo) (error :bar))'
        result = eval_str(exp)
        self.assertEqual(result, Bool(False))

    def test_bad_eq(self):
        exp = '(eq (error :foo) :bar :buz)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = '(eq :foo)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = '(eq)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_good_if(self):
        exp = '(if (error :foo) 100 200)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

        exp = '(if #t (error :foo) 200)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

        exp = '(if #f (error :foo) 200)'
        result = eval_str(exp)
        self.assertEqual(result, 200)

        exp = '(if #f (error :foo) (error :bar))'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':bar'))

    def test_bad_if(self):
        exp = '(if (error :foo) 100)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = '(if (error :foo) 100 200 300)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = '(if nil 100 200)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

    def test_good_typeof(self):
        exp = '(typeof (error :foo))'
        result = eval_str(exp)
        self.assertEqual(result, Symbol('error'))

    def test_bad_typeof(self):
        exp = '(typeof 100 200)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = '(typeof)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

    def test_good_first(self):
        exp = "(first (error :foo))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

    def test_bad_first(self):
        exp = "(first '(1) '(2))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(first)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(first 10)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

        exp = '(first "foo")'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

        exp = '(first :foo)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

    def test_good_rest(self):
        exp = "(rest (error :foo))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

    def test_bad_rest(self):
        exp = "(rest '(1) '(2))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(rest)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(rest 10)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

        exp = '(rest "foo")'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

        exp = '(rest :foo)'
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

    def test_good_prep(self):
        exp = "(prep (error :foo) '(2 3))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

        exp = "(prep 1 (error :foo))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

    def test_bad_prep(self):
        exp = "(prep)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(prep 1 '() '())"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(prep 1 1)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

    def test_good_apply(self):
        exp = "(apply (error :foo) '())"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

        exp = "(apply (fn () 1) (error :foo))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':foo'))

    def test_bad_apply(self):
        exp = "(apply 10 '())"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

        exp = "(apply (fn (x) x) 10)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':type-error'))

        exp = "(apply (fn (x) x) '(1 2))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(apply (fn (x) x) '(1) '(1))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(apply (fn () 1))"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

        exp = "(apply)"
        result = eval_str(exp)
        self.assertEqual(result, create_error(':arg-error'))

if __name__ == '__main__':
    unittest.main()
