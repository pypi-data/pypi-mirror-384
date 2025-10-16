# payra-sdk-python/payra_sdk/order_verification.py

import os
import json
import random
from dotenv import load_dotenv
from web3 import Web3
from .utils import PayraUtils
from .exceptions import InvalidArgumentError, SignatureError

# load env
load_dotenv()

class PayraOrderVerification:
    """
    SDK for verifying if an order has been paid using the Payra smart contract.
    """

    def __init__(self, network: str):
        self.network = network.upper()
        self.rpc_url = self.get_rpc_url(self.network)

        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.web3.is_connected():
            raise ConnectionError(f"Failed to connect to QuickNode RPC for {self.network}")

        self.merchant_id = os.getenv(f"PAYRA_{self.network}_MERCHANT_ID")
        self.forward_address = os.getenv(f"PAYRA_{self.network}_CORE_FORWARD_CONTRACT_ADDRESS")

        if not self.merchant_id:
            raise InvalidArgumentError(f"Missing PAYRA_{self.network}_MERCHANT_ID in .env")
        if not self.forward_address:
            raise InvalidArgumentError(f"Missing PAYRA_{self.network}_CORE_FORWARD_CONTRACT_ADDRESS in .env")

        # Load ABI
        abi_path = os.path.join(os.path.dirname(__file__), "contracts", "payraABI.json")
        with open(abi_path, "r") as f:
            self.abi = json.load(f)

        # find ABI parts
        self.core_fn = PayraUtils.find_function(self.abi, "isOrderPaid")
        self.forward_fn = PayraUtils.find_function(self.abi, "forward")

        # prepare forward contract
        self.forward_contract = self.web3.eth.contract(
            address=self.web3.to_checksum_address(self.forward_address),
            abi=[self.forward_fn]
        )

    def get_rpc_url(self, network: str) -> str:
        """
        Collects all PAYRA_{NETWORK}_RPC_URL_i variables and randomly picks one.
        """
        urls = []
        i = 1
        while True:
            env_key = f"PAYRA_{network}_RPC_URL_{i}"
            value = os.getenv(env_key)
            if not value:
                break
            urls.append(value.strip())
            i += 1

        if not urls:
            raise InvalidArgumentError(f"No RPC URLs found for network: {network}")

        return random.choice(urls)

    def is_order_paid(self, order_id: str) -> dict:
        """
        Calls the Payra Forward contract to check if an order is paid.
        """
        try:
            # encode isOrderPaid call manually
            core_fn_selector = PayraUtils.function_selector(self.core_fn)
            encoded_params = self.web3.codec.encode(
                [inp["type"] for inp in self.core_fn["inputs"]],
                [int(self.merchant_id), order_id]
            )
            data = core_fn_selector + encoded_params.hex()

            # call forward()
            result = self.forward_contract.functions.forward("0x" + data).call()

            # decode result
            decoded = self.web3.codec.decode(
                [out["type"] for out in self.core_fn["outputs"]],
                result
            )

            return {
                "success": True,
                "paid": bool(decoded[0]),
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "paid": None,
                "error": str(e)
            }
