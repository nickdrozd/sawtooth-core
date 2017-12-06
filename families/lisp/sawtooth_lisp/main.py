import sys
import argparse

from sawtooth_sdk.processor.core import TransactionProcessor
from sawtooth_sdk.processor.config import get_log_dir
from sawtooth_sdk.processor.config import get_log_config
from sawtooth_sdk.processor.log import init_console_logging
from sawtooth_sdk.processor.log import log_configuration
from sawtooth_lisp.handler import LispHandler


def parse_args(args):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('endpoint',
                        nargs='?',
                        default='tcp://localhost:4004',
                        help='Endpoint for the validator connection')
    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Increase output sent to stderr')

    return parser.parse_args(args)


def main(args=sys.argv[1:]):
    opts = parse_args(args)

    processor = TransactionProcessor(url=opts.endpoint)
    log_config = get_log_config(filename="lisp_log_config.toml")
    if log_config is not None:
        log_configuration(log_config=log_config)
    else:
        log_dir = get_log_dir()
        # use the transaction processor zmq identity for filename
        log_configuration(
            log_dir=log_dir,
            name="lisp-" + str(processor.zmq_id)[2:-1])

    init_console_logging(verbose_level=opts.verbose)

    processor.add_handler(LispHandler())

    try:
        processor.start()
    except KeyboardInterrupt:
        pass
    finally:
        processor.stop()
