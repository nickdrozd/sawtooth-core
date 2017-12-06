import unittest
import time
import logging
import json
from base64 import b64decode

from sawtooth_integration.tests.lisp_client import LispClient
from sawtooth_integration.tests.integration_tools import wait_for_rest_apis

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)


URL = 'http://rest-api:8080'


class TestLisp(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.client = LispClient(URL)
        wait_for_rest_apis(['rest-api:8080'])

    def setUp(self):
        self.name = None
        self.expr = None
        self.expected_result = None

    def test_lisp_numbers(self):
        self.name = 'NUMBERS'

        self.expr = [
            ['lambda', ['x', 'y'],
                ['*', ['+', 'x', 'y'],
                      ['-', 'x', 'y']]],
            ['/', 24, 4],
            3
        ]

        self.expected_result = 27

        LOGGER.error(self.client.get_data())

        self.run_and_check()

    ###

    def test_church_encoding(self):
        self.name = 'CHURCH'

        zero = ['lambda', ['f'],
                    ['lambda', ['x'],
                        'x']]

        one = ['lambda', ['f'],
                    ['lambda', ['x'],
                        ['f', 'x']]]

        two = ['lambda', ['f'],
                    ['lambda', ['x'],
                        ['f', ['f', 'x']]]]

        add = ['lambda', ['n'],
                    ['lambda', ['m'],
                        ['lambda', ['f'],
                            ['lambda', ['x'],
                                [['n', 'f'], [['m', 'f'], 'x']]]]]]

        church_expr = [[add, [[add, one], zero]], [[add, two], two]]

        self.expr = [[church_expr, ['lambda', ['n'], ['+', 'n', 1]]], 0]

        self.expected_result = 5

        self.run_and_check()

    @unittest.skip('This one will never terminate.')
    def test_loop(self):
        self.name = 'LOOP'

        self.expr = [['lambda', ['f'], ['f', 'f']],
                       ['lambda', ['f'], ['f', 'f']]]

        self.expected_result = '???'

        self.run_and_check()

    ###

    def run_and_check(self):
        self.declare()
        self.run_lisp()
        self.assert_result()

    def assert_result(self):
        LOGGER.info(
            'Asserting {} to be {}'.format(
                self.name,
                self.expected_result))

        self.assertEqual(
            self.client.check_result(self.name),
            self.expected_result)

    def declare(self):
        LOGGER.info(
            'Declaring {} to be {}'.format(
                self.name,
                self.expr))

        self.client.declare(
            self.name,
            self.expr)

        time.sleep(1)

    def run_lisp(self):
        while not self.client.is_done(self.name):
            self.client.step(self.name)

            state = b64decode(self.client.list_state()['data'][0]['data']).decode()
            for register, value in sorted(json.loads(state).items()):
                LOGGER.debug('{}: {}'.format(register, value))

        time.sleep(1)
