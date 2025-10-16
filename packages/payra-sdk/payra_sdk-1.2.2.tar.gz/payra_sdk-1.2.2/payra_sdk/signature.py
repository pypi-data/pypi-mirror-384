# payra-sdk-python/payra_sdk/signature.py

import os
import time
from dotenv import load_dotenv
from eth_abi import encode
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import keccak, to_checksum_address
from .exceptions import InvalidArgumentError, SignatureError

# Load environment variables from .env file
load_dotenv()

class PayraSignatureGenerator:
    """
    SDK for generating Payra payment signatures on the backend.
    This version assumes `amount_wei` is already in the token's smallest unit (e.g., wei)
    and does not require connecting to a blockchain RPC for decimals lookup.
    """

    def __init__(self):

        """
        Initializes the PayraSignatureGenerator.
        """

    def generate_signature(
        self,
        network: str,
        token_address: str,
        order_id: str,
        amount_wei: int,      # Expected as int (already in smallest units)
        timestamp: int,
        payer_address: str
    ) -> str:
        """
        Generates a Payra compatible signature for a payment request.

        This method mirrors the logic of the JavaScript `generateSignature` function,
        but operates offline with `amount_wei` already converted to its smallest unit.

        Args:
            token_address (str): The ERC20 token contract address (e.g., USDT, USDC).
            merchant_id (int): The merchant's unique ID.
            order_id (str): The unique order ID for this transaction.
            amount_wei (int): The payment amount in the token's smallest units (e.g., wei for ETH,
                          or 10^decimals for ERC20, already pre-calculated by frontend).
            timestamp (int, optional): Unix timestamp in seconds. If None, current time is used.

        Returns:
            str: The 0x-prefixed hex string of the generated signature.

        Raises:
            InvalidArgumentError: If any required argument is missing or invalid.
            SignatureError: If the signature generation process fails.
        """

        private_key, merchant_id = self.get_credentials_for_network(network)

        try:
            self.signer_account = Account.from_key(private_key)
        except Exception as e:
            raise SignatureError(f"Failed to initialize signer account from private key: {e}")

        # Basic validation of input types and presence
        if not isinstance(token_address, str) or not token_address.startswith('0x'):
            raise InvalidArgumentError("token_address must be a 0x-prefixed string.")
        if not isinstance(merchant_id, int) or merchant_id < 0:
            raise InvalidArgumentError("merchant_id must be a non-negative integer.")
        if not isinstance(order_id, str) or not order_id:
            raise InvalidArgumentError("order_id must be a non-empty string.")
        if not isinstance(amount_wei, int) or amount_wei < 0:
            raise InvalidArgumentError("amount_wei must be a non-negative integer (in smallest units).")
        if not isinstance(timestamp, int) or timestamp < 0: # <--- Dodano walidację timestampu
            raise InvalidArgumentError("timestamp must be a non-negative integer and provided by frontend.")
        if not isinstance(payer_address, str) or not payer_address.startswith('0x'):
            raise InvalidArgumentError("payer_address must be a 0x-prefixed string.")

        checksum_token_address = to_checksum_address(token_address)
        checksum_payer_address = to_checksum_address(payer_address)

        try:
            # 1. ABI Encode the data
            # ['address', 'uint256', 'string', 'uint256', 'uint256', 'address'],
            # [formState.token, BigInt(formState.merchantId), formState.orderId, amountInWei, BigInt(currentTimestamp)]
            encoded_data = encode(
                ['address', 'uint256', 'string', 'uint256', 'uint256', 'address'],[
                    checksum_token_address,
                    merchant_id,        # merchantId as uint256
                    order_id,           # orderId as string
                    amount_wei,             # amount_wei (already in smallest units) as uint256
                    timestamp,          # timestamp as uint256
                    checksum_payer_address
                ]
            )

            # 2. Keccak256 hash the encoded data
            # JS: ethers.keccak256(encodedData)
            # This hashes the raw bytes, NOT adding the 'Ethereum Signed Message' prefix.
            message_hash = keccak(encoded_data)

            # 3. Sign the message hash
            # JS: signer.signMessage(ethers.getBytes(messageHash))
            # eth_account's encode_defunct(primitive=message_hash) mimics ethers.getBytes(messageHash)
            # by wrapping the raw hash without adding the standard Ethereum message prefix.
            message_to_sign = encode_defunct(primitive=message_hash)
            signed_message = self.signer_account.sign_message(message_to_sign)

            # Return the full signature as a hex string (v, r, s concatenated)
            return '0x' + signed_message.signature.hex()

        except InvalidArgumentError:
            raise # Re-raise directly as it's already a PayraSDKException
        except Exception as e:
            # Catch any other unexpected errors during signature generation
            raise SignatureError(f"Error generating signature: {e}")

    # Optional: Add a verification method if you ever need to verify a signature offline
    def verify_signature(
        self,
        network: str,
        token_address: str,
        order_id: str,
        amount_wei: int,
        timestamp: int,
        payer_address: str,
        signature: str
    ) -> str:
        """
        Verifies a Payra signature by recovering the signer address.
        Useful for internal validation.

        Returns:
            str: The 0x-prefixed checksummed address of the signer.
        """
        private_key, merchant_id = self.get_credentials_for_network(network)

        # First, generate the message hash exactly as it was generated for signing
        message_hash = self.generate_message_hash(
            token_address=token_address,
            merchant_id=merchant_id,
            order_id=order_id,
            amount_wei=amount_wei,
            timestamp=timestamp,
            payer_address=payer_address
        )

        try:
            # Recreate the message to sign exactly as it was created
            message_to_recover = encode_defunct(primitive=message_hash)
            recovered_address = Account.recover_message(
                message_to_recover,
                signature=signature
            )
            return to_checksum_address(recovered_address)
        except Exception as e:
            raise SignatureError(f"Failed to recover signer address for verification: {e}")

    def generate_message_hash(
        self,
        token_address: str,
        merchant_id: int,
        order_id: str,
        amount_wei: int,
        timestamp: int,
        payer_address: str
    ) -> bytes:
        """
        Generates the raw Keccak256 hash of the ABI-encoded payment data.
        This is a helper for internal use, especially for `verify_signature`.
        """
        checksum_token_address = to_checksum_address(token_address)
        checksum_payer_address = to_checksum_address(payer_address)
        encoded_data = encode(
            ['address', 'uint256', 'string', 'uint256', 'uint256', 'address'],[
                checksum_token_address,
                merchant_id,
                order_id,
                amount_wei,
                timestamp,
                checksum_payer_address
            ]
        )
        return keccak(encoded_data)

    # get network env
    def get_credentials_for_network(self, network: str) -> tuple[str, int]:
        """
        Returns (private_key, merchant_id) for the given network using dynamic env keys like:
        PAYRA_POLYGON_PRIVATE_KEY, PAYRA_POLYGON_MERCHANT_ID
        """

        private_key = os.getenv(f"PAYRA_{network.upper()}_PRIVATE_KEY")
        merchant_id = os.getenv(f"PAYRA_{network.upper()}_MERCHANT_ID")

        if not private_key or not merchant_id:
            raise ValueError(f"Missing credentials for network '{network}' in .env (checked {private_key_key}, {merchant_id_key})")

        return private_key, int(merchant_id)

    def get_account_address(self, network: str) -> str:
        private_key, merchant_id = self.get_credentials_for_network(network)
        account = Account.from_key(private_key)

        return account.address
