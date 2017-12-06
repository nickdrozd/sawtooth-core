import json

from sawtooth_lisp.lisp import LISP_NAMESPACE
from sawtooth_processor_test.message_factory import MessageFactory


class LispMessageFactory:
    def __init__(self, private=None, public=None):
        self.family_name = 'lisp'

        self._factory = MessageFactory(
            family_name=self.family_name,
            family_version='1.0',
            namespace=LISP_NAMESPACE)

    def create_transaction(self, cmd, name, expr=''):
        data = {
            'cmd': cmd,
            'name': name,
            'expr': expr
        }

        payload = json.dumps(data).encode()

        addresses = [self.name_to_address(name)]

        return self._factory.create_transaction(
            payload=payload,
            inputs=addresses,
            outputs=addresses,
            deps=[])

    def create_batch(self, cmd, name, expr):
        txn = self.create_transaction(cmd, name, expr)

        return self._factory.create_batch([txn])

    def name_to_address(self, name):
        return LISP_NAMESPACE + self._factory.sha512(name.encode())[:64]
