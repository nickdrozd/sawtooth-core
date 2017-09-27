# Copyright 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------

import unittest

from rpc_client import RpcClient
from mock_validator import MockValidator

from sawtooth_sdk.protobuf.validator_pb2 import Message
from sawtooth_sdk.protobuf.client_pb2 import ClientBlockListRequest
from sawtooth_sdk.protobuf.client_pb2 import ClientBlockListResponse
from sawtooth_sdk.protobuf.client_pb2 import ClientBlockGetRequest
from sawtooth_sdk.protobuf.client_pb2 import ClientBlockGetResponse
from sawtooth_sdk.protobuf.block_pb2 import Block
from sawtooth_sdk.protobuf.block_pb2 import BlockHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.txn_receipt_pb2 import ClientReceiptGetRequest
from sawtooth_sdk.protobuf.txn_receipt_pb2 import ClientReceiptGetResponse
from sawtooth_sdk.protobuf.txn_receipt_pb2 import TransactionReceipt
from protobuf.seth_pb2 import SethTransactionReceipt


class SethRpcTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = MockValidator()
        cls.validator.listen("tcp://eth0:4004")
        cls.url = 'http://seth-rpc:3030/'
        cls.rpc = RpcClient(cls.url)
        cls.rpc.wait_for_service()

    # Network tests
    def test_net_version(self):
        """Test that the network id 19 is returned."""
        self.assertEqual("19", self.rpc.call("net_version"))

    def test_net_peerCount(self):
        """Test that 0 is returned as hex."""
        self.assertEqual("0x0", self.rpc.call("net_peerCount"))

    def test_net_listening(self):
        """Test that the True is returned."""
        self.assertEqual(True, self.rpc.call("net_listening"))

    # Block tests
    def test_block_number(self):
        """Test that the block number is extracted correctly and returned as
        hex."""
        self.rpc.acall("eth_blockNumber")
        msg = self.validator.receive()
        self.assertEqual(msg.message_type, Message.CLIENT_BLOCK_LIST_REQUEST)
        self.validator.respond(
            Message.CLIENT_BLOCK_LIST_RESPONSE,
            ClientBlockListResponse(
                status=ClientBlockListResponse.OK,
                blocks=[Block(
                    header=BlockHeader(block_num=15).SerializeToString(),
                )]),
            msg)
        self.assertEqual("0xf", self.rpc.get_result())

    def test_get_block_by_hash(self):
        """Test that a block is retrieved correctly, given a block id."""
        self._test_get_block(by="hash")

    def test_get_block_by_number(self):
        """Test that a block is retrieved correctly, given a block number."""
        self._test_get_block(by="number")

    def _test_get_block(self, by):
        block_id = "f" * 128
        block_num = 123
        prev_block_id = "e" * 128
        state_root = "d" * 64
        txn_id = "c" * 64
        gas = 456
        if by == "hash":
            self.rpc.acall("eth_getBlockByHash", ["0x" + block_id, False])
        elif by == "number":
            self.rpc.acall("eth_getBlockByNumber", [hex(block_num), False])

        # Verify block get request
        msg = self.validator.receive()
        self.assertEqual(msg.message_type, Message.CLIENT_BLOCK_GET_REQUEST)
        request = ClientBlockGetRequest()
        request.ParseFromString(msg.content)
        if by == "hash":
            self.assertEqual(request.block_id[2:], block_id)
        elif by == "number":
            self.assertEqual(request.block_num, block_num)

        self.validator.respond(
            Message.CLIENT_BLOCK_GET_RESPONSE,
            ClientBlockGetResponse(
                status=ClientBlockGetResponse.OK,
                block=Block(
                    header=BlockHeader(
                        block_num=block_num,
                        previous_block_id=prev_block_id,
                        state_root_hash=state_root
                    ).SerializeToString(),
                    header_signature=block_id,
                    batches=[Batch(transactions=[Transaction(
                        header=TransactionHeader(
                            family_name="seth",
                        ).SerializeToString(),
                        header_signature=txn_id,
                    )])],
                )
            ),
            msg)

        # Verify receipt get request
        msg = self.validator.receive()
        self.assertEqual(msg.message_type, Message.CLIENT_RECEIPT_GET_REQUEST)
        request = ClientReceiptGetRequest()
        request.ParseFromString(msg.content)
        self.assertEqual(request.transaction_ids[0], txn_id)

        self.validator.respond(
            Message.CLIENT_RECEIPT_GET_RESPONSE,
            ClientReceiptGetResponse(
                status=ClientReceiptGetResponse.OK,
                receipts=[TransactionReceipt(
                    data=[TransactionReceipt.Data(
                        data_type="seth_receipt",
                        data=SethTransactionReceipt(
                            gas_used=gas,
                        ).SerializeToString(),
                    )],
                    transaction_id=txn_id,
                )]
            ),
            msg)

        result = self.rpc.get_result()
        self.assertEqual(result["number"], hex(block_num))
        self.assertEqual(result["hash"], "0x" + block_id)
        self.assertEqual(result["parentHash"], "0x" + prev_block_id)
        self.assertEqual(result["stateRoot"], "0x" + state_root)
        self.assertEqual(result["gasUsed"], hex(gas))
        self.assertEqual(result["transactions"][0], "0x" + txn_id)