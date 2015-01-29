import parable

import unittest

class ParableCoreTest(unittest.TestCase):
    def eval_str(self, s):
        exp = parable.parse_str(s)
        return parable.eval(exp, {})

    def test_if(self):
        exp = '(if (quote t) (quote a) (quote b))'
        result = self.eval_str(exp)
        self.assertEqual(result, 'a')

        exp = '(if (quote ()) (quote a) (quote b))'
        result = self.eval_str(exp)
        self.assertEqual(result, 'b')

    def test_quote(self):
        exp = '(quote x)'
        result = self.eval_str(exp)
        self.assertEqual(result, 'x')

    def test_atom(self):
        exp = '(atom (quote x))'
        result = self.eval_str(exp)
        self.assertNotEqual(result, [])

        exp = '(atom (quote (x y)))'
        result = self.eval_str(exp)
        self.assertEqual(result, [])

    def test_car(self):
        exp = '(car (quote (x y z)))'
        result = self.eval_str(exp)
        self.assertEqual(result, 'x')

    def test_cdr(self):
        exp = '(cdr (quote (x y z)))'
        result = self.eval_str(exp)
        self.assertEqual(result, ['y', 'z'])

    def test_cons(self):
        exp = '(cons (quote x) (quote (y z)))'
        result = self.eval_str(exp)
        self.assertEqual(result, ['x', 'y', 'z'])

    def test_eq(self):
        exp = '(eq (quote x) (quote x))'
        result = self.eval_str(exp)
        self.assertNotEqual(result, [])

        exp = '(eq (quote x) (quote y))'
        result = self.eval_str(exp)
        self.assertEqual(result, [])

        exp = '(eq (quote (a b)) (quote (a b)))'
        result = self.eval_str(exp)
        self.assertEqual(result, [])

    def test_function_call(self):
        exp = '((fn (a b c) b) (quote a) (quote b) (quote c))'
        result = self.eval_str(exp)
        self.assertEqual(result, 'b')

    def test_macro_call(self):
        exp = '((mac (a b c) b) (a b) (if (quote t) (quote a) (quote b)) (p q))'
        result = self.eval_str(exp)
        self.assertEqual(result, 'a')

if __name__ == '__main__':
    unittest.main()
