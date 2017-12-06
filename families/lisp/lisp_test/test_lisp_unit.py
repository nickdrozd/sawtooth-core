import unittest

from sawtooth_lisp.lisp import lisp_eval, initialize


class TestLisp(unittest.TestCase):
    def test_lisp(self):
        test_vals = {
            2: 2,

            ('+', 4, 5): 9,

            (('λ', ('x',), 'x'), 6): 6,

            (('λ', ('a', 'b'), ('*', 'a', 'b')), 7, 8): 56,

            (('λ', (), 9),): 9,

            ((('λ', (), '-'),),
                (('λ', ('x',), ('*', 'x', 'x')), 5),
                (('λ', ('x', 'y'), ('+', 'x', 'y')), 6, 7)): 12,

            ('if', ('>', 3, 2), 8, 9): 8,

            ('if', ('<', 3, 2), 8, 9): 9,
        }

        for expr, val in test_vals.items():
            self.assert_lisp_val(expr, val)

    def test_church(self):
        zero = ('λ', ('f',),
                ('λ', ('x',),
                    'x'))

        one = ('λ', ('f',),
                ('λ', ('x',),
                    ('f', 'x')))

        two = ('λ', ('f',),
                ('λ', ('x',),
                    ('f', ('f', 'x'))))

        add = ('λ', ('n',),
                ('λ', ('m',),
                    ('λ', ('f',),
                        ('λ', ('x',),
                            (('n', 'f'),
                                (('m', 'f'), 'x'))))))

        test_vals = {
            zero: 0,
            one: 1,
            two: 2,
            ((add, one), two): 3,
            ((add, ((add, one), zero)), ((add, two), two)): 5
        }

        for expr, val in test_vals.items():
            converted = ((expr, ('λ', ('n',), ('+', 'n', 1))), 0)
            self.assert_lisp_val(converted, val)

    def assert_lisp_val(self, expr, expected):
        data = initialize(expr)

        while data['instr'] != 'DONE':
            data = lisp_eval(data)

        result = data['val']

        self.assertEqual(
            result,
            expected)
