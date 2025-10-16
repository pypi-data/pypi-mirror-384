"""Python client template."""

import datetime
from typing import Any, Literal, Union
from uuid import UUID

from jsonrpc2pyclient.decorator import Transportable, rpc_class_method
from jsonrpc2pyclient.httpclient import AsyncRPCHTTPClient
from jsonrpc2pyclient.rpcclient import AsyncRPCClient, RPCClient
from py_undefined import Undefined
from pydantic import UUID1, UUID3, UUID4, UUID5


ClientType = Union[AsyncRPCClient, RPCClient]
CLIENT_URL = "example.com"


class AeriumOpenRPCClient(Transportable):
    def __init__(
        self, headers: dict[str, Any], client_url: str = CLIENT_URL, **kwargs: Any
    ) -> None:
        transport = AsyncRPCHTTPClient(client_url, headers, **kwargs)
        self.aerium = AeriumOpenRPCClient._AeriumClient(transport)
        super().__init__(transport)

    class _AeriumClient(Transportable):
        def __init__(self, transport: ClientType) -> None:
            self.transaction = AeriumOpenRPCClient._AeriumClient._TransactionClient(
                transport
            )
            self.blockchain = AeriumOpenRPCClient._AeriumClient._BlockchainClient(
                transport
            )
            self.network = AeriumOpenRPCClient._AeriumClient._NetworkClient(transport)
            self.utils = AeriumOpenRPCClient._AeriumClient._UtilsClient(transport)
            self.wallet = AeriumOpenRPCClient._AeriumClient._WalletClient(transport)
            super().__init__(transport)

        class _TransactionClient(Transportable):
            @rpc_class_method(method_name="aerium.transaction.get_transaction")
            async def get_transaction(
                self, id: str = Undefined, verbosity: int = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.transaction.calculate_fee")
            async def calculate_fee(
                self,
                amount: int = Undefined,
                payload_type: int = Undefined,
                fixed_amount: bool = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.transaction.broadcast_transaction")
            async def broadcast_transaction(
                self, signed_raw_transaction: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(
                method_name="aerium.transaction.get_raw_transfer_transaction"
            )
            async def get_raw_transfer_transaction(
                self,
                lock_time: int = Undefined,
                sender: str = Undefined,
                receiver: str = Undefined,
                amount: int = Undefined,
                fee: int = Undefined,
                memo: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.transaction.get_raw_bond_transaction")
            async def get_raw_bond_transaction(
                self,
                lock_time: int = Undefined,
                sender: str = Undefined,
                receiver: str = Undefined,
                stake: int = Undefined,
                public_key: str = Undefined,
                fee: int = Undefined,
                memo: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(
                method_name="aerium.transaction.get_raw_unbond_transaction"
            )
            async def get_raw_unbond_transaction(
                self,
                lock_time: int = Undefined,
                validator_address: str = Undefined,
                memo: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(
                method_name="aerium.transaction.get_raw_withdraw_transaction"
            )
            async def get_raw_withdraw_transaction(
                self,
                lock_time: int = Undefined,
                validator_address: str = Undefined,
                account_address: str = Undefined,
                amount: int = Undefined,
                fee: int = Undefined,
                memo: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(
                method_name="aerium.transaction.get_raw_batch_transfer_transaction"
            )
            async def get_raw_batch_transfer_transaction(
                self,
                lock_time: int = Undefined,
                sender: str = Undefined,
                recipients: list[dict[str, Any]] = Undefined,
                fee: int = Undefined,
                memo: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.transaction.decode_raw_transaction")
            async def decode_raw_transaction(
                self, raw_transaction: str = Undefined
            ) -> dict[str, Any]: ...

        class _BlockchainClient(Transportable):
            @rpc_class_method(method_name="aerium.blockchain.get_block")
            async def get_block(
                self, height: int = Undefined, verbosity: int = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_block_hash")
            async def get_block_hash(
                self, height: int = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_block_height")
            async def get_block_height(
                self, hash: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_blockchain_info")
            async def get_blockchain_info(self) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_consensus_info")
            async def get_consensus_info(self) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_account")
            async def get_account(self, address: str = Undefined) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_validator")
            async def get_validator(
                self, address: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_validator_by_number")
            async def get_validator_by_number(
                self, number: int = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_validator_addresses")
            async def get_validator_addresses(self) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_public_key")
            async def get_public_key(
                self, address: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.blockchain.get_tx_pool_content")
            async def get_tx_pool_content(
                self, payload_type: int = Undefined
            ) -> dict[str, Any]: ...

        class _NetworkClient(Transportable):
            @rpc_class_method(method_name="aerium.network.get_network_info")
            async def get_network_info(
                self, only_connected: bool = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.network.get_node_info")
            async def get_node_info(self) -> dict[str, Any]: ...

        class _UtilsClient(Transportable):
            @rpc_class_method(method_name="aerium.utils.sign_message_with_private_key")
            async def sign_message_with_private_key(
                self, private_key: str = Undefined, message: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.utils.verify_message")
            async def verify_message(
                self,
                message: str = Undefined,
                signature: str = Undefined,
                public_key: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.utils.public_key_aggregation")
            async def public_key_aggregation(
                self, public_keys: list[str] = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.utils.signature_aggregation")
            async def signature_aggregation(
                self, signatures: list[str] = Undefined
            ) -> dict[str, Any]: ...

        class _WalletClient(Transportable):
            @rpc_class_method(method_name="aerium.wallet.create_wallet")
            async def create_wallet(
                self, wallet_name: str = Undefined, password: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.restore_wallet")
            async def restore_wallet(
                self,
                wallet_name: str = Undefined,
                mnemonic: str = Undefined,
                password: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.load_wallet")
            async def load_wallet(
                self, wallet_name: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.unload_wallet")
            async def unload_wallet(
                self, wallet_name: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_total_balance")
            async def get_total_balance(
                self, wallet_name: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.sign_raw_transaction")
            async def sign_raw_transaction(
                self,
                wallet_name: str = Undefined,
                raw_transaction: str = Undefined,
                password: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_validator_address")
            async def get_validator_address(
                self, public_key: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_new_address")
            async def get_new_address(
                self,
                wallet_name: str = Undefined,
                address_type: int = Undefined,
                label: str = Undefined,
                password: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_address_history")
            async def get_address_history(
                self, wallet_name: str = Undefined, address: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.sign_message")
            async def sign_message(
                self,
                wallet_name: str = Undefined,
                password: str = Undefined,
                address: str = Undefined,
                message: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_total_stake")
            async def get_total_stake(
                self, wallet_name: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_address_info")
            async def get_address_info(
                self, wallet_name: str = Undefined, address: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.set_address_label")
            async def set_address_label(
                self,
                wallet_name: str = Undefined,
                password: str = Undefined,
                address: str = Undefined,
                label: str = Undefined,
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.list_wallet")
            async def list_wallet(self) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.get_wallet_info")
            async def get_wallet_info(
                self, wallet_name: str = Undefined
            ) -> dict[str, Any]: ...
            @rpc_class_method(method_name="aerium.wallet.list_address")
            async def list_address(
                self, wallet_name: str = Undefined
            ) -> dict[str, Any]: ...
