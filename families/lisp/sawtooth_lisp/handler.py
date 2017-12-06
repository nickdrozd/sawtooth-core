from sawtooth_lisp import lisp
from sawtooth_lisp.simple_handler import SimpleHandler


class LispHandler(SimpleHandler):
    def __init__(self):
        super().__init__(
            family_name='lisp',
            txn_decode_function=lisp.txn_decode,
            state_decode_function=lisp.state_decode,
            state_encode_function=lisp.state_encode,
            execution_function=lisp.lisp_commands,
        )
