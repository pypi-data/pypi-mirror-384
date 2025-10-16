# payra-sdk-python/payra_sdk/utils.py

import os
import time
import requests
from web3 import Web3
from typing import Any, Dict, Union
from .exceptions import InvalidArgumentError

class PayraUtils:
    """
    Utility helper for Payra SDK.
    Provides helper methods for conversions and ABI-related operations.
    """

    _cache_data = None
    _cache_timestamp = 0
    _cache_ttl = 720 * 60

    @staticmethod
    def find_function(abi: list[Dict[str, Any]], name: str) -> Dict[str, Any]:
        """
        Finds a function definition by name in the given ABI.
        """
        for entry in abi:
            if entry.get("type") == "function" and entry.get("name") == name:
                return entry
        raise InvalidArgumentError(f"Function {name} not found in ABI!")

    @staticmethod
    def function_selector(fn: Dict[str, Any]) -> str:
        """
        Generates the function selector (first 4 bytes of keccak of signature).
        """
        signature = f"{fn['name']}({','.join([inp['type'] for inp in fn['inputs']])})"
        return Web3.keccak(text=signature)[:4].hex()

    # === Conversion Helpers ===
    @staticmethod
    def to_wei(amount: Union[int, float, str], chain: str, token: str) -> int:
        """
        Converts USD or token amount to Wei.
        Equivalent of `PayraUtils::toWei()` in PHP SDK.
        """
        decimals = PayraUtils.get_decimals(chain, token)
        return int(float(amount) * (10 ** decimals))

    @staticmethod
    def from_wei(amount_wei: Union[int, str], chain: str, token: str, precision: int = 2) -> str:
        """
        Converts Wei to USD or token amount.
        Equivalent of `PayraUtils::fromWei()` in PHP SDK.
        """
        decimals = PayraUtils.get_decimals(chain, token)
        value = int(amount_wei) / (10 ** decimals)
        return f"{value:.{precision}f}"

    # === Internal ===
    @staticmethod
    def get_decimals(chain: str, token: str) -> int:
        """
        Returns the number of decimals for a given chain/token pair.
        Extend as needed for more tokens.
        """
        token = token.lower()
        chain = chain.lower()

        mapping = {
            "polygon": {"usdt": 6, "usdc": 6, "pol": 18},
        }

        try:
            return mapping[chain][token]
        except KeyError:
            raise InvalidArgumentError(f"Unsupported token '{token}' on chain '{chain}'.")

    # === Exchange Rates ===
    @staticmethod
    def convert_to_usd(amount: float, from_currency: str) -> float:
        """
        Converts a given amount from another currency to USD using the ExchangeRate API.
        Requires:
          - EXCHANGE_RATE_API_KEY (API key only)
          - optional EXCHANGE_RATE_CACHE_TIME (minutes)
        """

        api_key = os.getenv("EXCHANGE_RATE_API_KEY")
        if not api_key:
            raise InvalidArgumentError("EXCHANGE_RATE_API_KEY is not set in .env")

        # TTL in minutes (if not exists, use default 720)
        cache_minutes = int(os.getenv("EXCHANGE_RATE_CACHE_TIME", 720))
        PayraUtils._cache_ttl = cache_minutes * 60

        api_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
        from_currency = from_currency.upper()

        current_time = time.time()

        # use cache if < TTL
        if (
            PayraUtils._cache_data is not None
            and (current_time - PayraUtils._cache_timestamp) < PayraUtils._cache_ttl
        ):
            data = PayraUtils._cache_data
        else:
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                data = response.json()

                PayraUtils._cache_data = data
                PayraUtils._cache_timestamp = current_time
            except requests.RequestException as e:
                raise InvalidArgumentError(f"Failed to connect to ExchangeRate API: {e}")
            except (KeyError, ValueError) as e:
                raise InvalidArgumentError(f"Invalid data from ExchangeRate API: {e}")

        if "conversion_rates" not in data or from_currency not in data["conversion_rates"]:
            raise InvalidArgumentError(f"Conversion rate for {from_currency} not found in API response")

        rate = data["conversion_rates"][from_currency]
        usd_value = round(amount / rate, 2)
        return usd_value
