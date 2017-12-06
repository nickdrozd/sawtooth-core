import json

from sawtooth_lisp.lisp import LISP_NAMESPACE
from lisp_test.lisp_message_factory import LispMessageFactory
from sawtooth_integration.tests.integration_tools import RestClient


class LispClient(RestClient):
    def __init__(self, url):
        super().__init__(url, LISP_NAMESPACE)
        self.factory = LispMessageFactory()

    def declare(self, name, expr):
        return self._send_lisp_txn(
            'declare', name, expr)

    def step(self, name):
        return self._send_lisp_txn(
            'step', name, '')

    def show(self, name):
        return self.get_leaf(self.make_address(name)).decode()

    def list(self):
        pass

    def get_register(self, name, register):
        return json.loads(
            self.show(name))[register]

    def check_result(self, name):
        return self.get_register(name, 'val')

    def is_done(self, name):
        return self.get_register(name, 'instr') == 'DONE'

    def _send_lisp_txn(self, cmd, name, expr=''):
        return self.send_batches(
            self.factory.create_batch(
                cmd, name, expr))

    def make_address(self, name):
        return self.factory.name_to_address(name)
