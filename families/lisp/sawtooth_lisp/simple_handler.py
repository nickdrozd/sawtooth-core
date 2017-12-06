import hashlib
import logging

from sawtooth_sdk.processor.exceptions import (
    InvalidTransaction,
    InternalError,
)


LOGGER = logging.getLogger(__name__)


class SimpleHandler:
    def __init__(self, family_name,
                 txn_decode_function,
                 state_decode_function,
                 state_encode_function,
                 execution_function,
                 family_versions=['1.0']):
        self._family_name = family_name
        self._namespace_prefix = _hash_address(family_name)[:6]
        self._namespaces = [self._namespace_prefix]

        self._decode_txn = txn_decode_function
        self._decode_data = state_decode_function
        self._encode_data = state_encode_function
        self._execute = execution_function

        self._family_versions = family_versions

    @property
    def family_name(self):
        return self._family_name

    @property
    def family_versions(self):
        return self._family_versions

    @property
    def namespaces(self):
        return self._namespaces

    ###

    def apply(self, transaction, context):
        name, *txn_data = self._unpack_transaction(transaction)

        state_data = self._get_state_data(name, context)

        updated_data = self._execute(*txn_data, state_data)

        self._store_data(name, updated_data, context)

    def _unpack_transaction(self, transaction):
        try:
            return self._decode_txn(transaction.payload)
        except:
            raise InvalidTransaction('Invalid payload serialization')

    def _get_state_data(self, name, context):
        address = self._make_address(name)

        state_entries = context.get_state([address])

        try:
            return self._decode_data(state_entries[0].data)
        except IndexError:
            return None
        except Exception as e:
            raise InternalError('Failed to deserialize data: {}'.format(e))

    def _store_data(self, name, data, context):
        addresses = context.set_state({
            self._make_address(name): self._encode_data(data),
        })

        if not addresses:
            raise InternalError('State error')

    def _make_address(self, name):
        return self._namespace_prefix + _hash_address(name)[:64]


def _hash_address(data):
    return hashlib.sha512(data.encode('utf-8')).hexdigest()
