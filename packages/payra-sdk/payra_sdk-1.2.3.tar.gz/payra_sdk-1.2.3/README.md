

# Payra Python SDK

Official Python SDK for integrating **Payra's on-chain payment system** into your backend applications.

This SDK provides:
- Secure generation of **ECDSA signatures** compatible with the Payra smart contract — used for order payment verification.
- Simple methods for **checking the on-chain status of orders** to confirm completed payments.

## How It Works

The typical flow for signing and verifying a Payra transaction:

1. The **frontend** prepares all required payment parameters:
   - **Network** – blockchain name (e.g. Polygon, Linea)
   - **Token address** – ERC-20 token contract address
   - **Order ID** – unique order identifier
   - **AmountWei** – already converted to the smallest unit (e.g. wei, 10⁶)
   - **Timestamp** – Unix timestamp of the order
   - **Payer wallet address**

2. The frontend sends these parameters to your **backend**.
3. The **backend** uses this SDK to generate a cryptographic **ECDSA signature** with its private key (performed **offline**).
4. The backend returns the generated signature to the frontend.
5. The **frontend** calls the Payra smart contract (`payOrder`) with all parameters **plus** the signature.

This process ensures full compatibility between your backend and Payra’s on-chain verification logic.

## Features

- Generates **Ethereum ECDSA signatures** using the `secp256k1` curve.  
- Fully compatible with **Payra's Solidity smart contracts** (`ERC-1155` payment verification).  
- Includes built-in **ABI encoding and decoding** via [`web3.py`](https://github.com/ethereum/web3.py).  
- Supports environment-based configuration (`.env`) for managing multiple blockchain networks.  
- Verifies **order payment status directly on-chain** via RPC or blockchain explorer API.  
- Provides **secure backend integration** using merchant private keys.  
- Includes optional utility helpers for:
  - **Currency conversion** (via [ExchangeRate API](https://www.exchangerate-api.com/))  
  - **USD ⇄ WEI** conversion for token precision handling.  

## Setup

Before installing this package, make sure you have an active **Payra** account:

👉 [https://payra.cash](https://payra.cash)

You will need:

- Your **Merchant ID** (unique for each blockchain network)  
- Your **Private Key** (used to sign Payra transactions securely)

Additionally:

- Create a free account at [QuickNode](https://www.quicknode.com/) to obtain your **RPC URLs** - these are required for reading on-chain order statuses directly from the blockchain.

Optional (recommended):

- Create a free API key at [ExchangeRate API](https://www.exchangerate-api.com/)  
  to enable **automatic fiat → USD conversions** using the built-in utility helpers.

## Installation

### From PyPI

Install the latest stable version from [PyPI](https://pypi.org/project/payra-sdk/):

```bash
pip install payra-sdk
```

### From Source (for development)

Clone and install locally (editable mode for development):

```bash
git clone https://github.com/payracash/payra-sdk-python.git
cd payra-sdk-python

python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -e .
```

### Dependencies

This SDK requires:
- **Python 3.8+**
- **web3.py**
- **ecdsa**
- **python-dotenv**
-   _(optional)_  `requests`  and  `exchange-rate-api`  for fiat conversion utilities.

## Environment Configuration

Create a (`.env`) file in your project root (you can copy from example):

```bash
cp .env.example .env
```

This file stores your **private configuration** and connection settings for all supported networks.  Never commit  (`.env`)  to version control.

### Required Variables

#### Exchange Rate (optional)

Used for automatic fiat → USD conversions via the built-in Payra utilities.

```bash
EXCHANGE_RATE_API_KEY=         # Your ExchangeRate API key (from exchangerate-api.com)
EXCHANGE_RATE_CACHE_TIME=720   # Cache duration in minutes (default: 720 = 12h)

PAYRA_POLYGON_CORE_FORWARD_CONTRACT_ADDRESS=0xf30070da76B55E5cB5750517E4DECBD6Cc5ce5a8
PAYRA_POLYGON_PRIVATE_KEY=
PAYRA_POLYGON_MERCHANT_ID=
PAYRA_POLYGON_RPC_URL_1=
PAYRA_POLYGON_RPC_URL_2=

PAYRA_ETHEREUM_CORE_FORWARD_CONTRACT_ADDRESS=
PAYRA_ETHEREUM_PRIVATE_KEY=
PAYRA_ETHEREUM_MERCHANT_ID=
PAYRA_ETHEREUM_RPC_URL_1=
PAYRA_ETHEREUM_RPC_URL_2=

PAYRA_LINEA_CORE_FORWARD_CONTRACT_ADDRESS=
PAYRA_LINEA_PRIVATE_KEY=
PAYRA_LINEA_MERCHANT_ID=
PAYRA_LINEA_RPC_URL_1=
PAYRA_LINEA_RPC_URL_2=
```

#### Important Notes

-   The cache automatically refreshes when it expires.    
-   You can adjust the cache duration by setting  `EXCHANGE_RATE_CACHE_TIME`:
    -   `5`  → cache for 5 minutes
    -   `60`  → cache for 1 hour
    -   `720`  → cache for 12 hours (default)
- Each network (Polygon, Ethereum, Linea) has its own  **merchant ID**,  **private key**, and  **RPC URLs**.  
- The SDK automatically detects which chain configuration to use based on the selected network.
- You can use multiple RPC URLs for redundancy (the SDK will automatically fall back if one fails).
- Contract addresses correspond to the deployed Payra Core Forward contracts per network.

## Usage Example

### Generating and verifying a Payra signature in your backend

```python
from payra_sdk import PayraUtils, PayraSignatureGenerator, PayraSDKException

try:
    # Convert amount to smallest unit (wei or token decimals)
    amount_wei = PayraUtils.to_wei(3.34, 'polygon', 'usdt')

    PAYMENT_DATA = {
        "network": "polygon",
        "tokenAddress": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",  # USDT on Polygon
        "orderId": "ORDER-1753824905006-301-322",
        "amountWei": amount_wei,  # e.g. 3.34 USDT in smallest unit
        "timestamp": 1753826059,  # current Unix timestamp
        "payerAddress": "0xe6c961D6ad9a27Ea8e5d99e40abaC365DE9Cc162"
    }

    # Initialize signer
    payra_signer = PayraSignatureGenerator()

    # Generate cryptographic signature
    signature = payra_signer.generate_signature(
        network=PAYMENT_DATA["network"],
        token_address=PAYMENT_DATA["tokenAddress"],
        order_id=PAYMENT_DATA["orderId"],
        amount_wei=PAYMENT_DATA["amountWei"],
        timestamp=PAYMENT_DATA["timestamp"],
        payer_address=PAYMENT_DATA["payerAddress"]
    )

    print(f"Generated signature: {signature}")

except PayraSDKException as e:
    print(f"Payra SDK error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

#### Behind the Scenes

1.  The backend converts the amount to the smallest blockchain unit (e.g. wei).
3.  A  `PayraSignatureGenerator`  instance is created using your private key from  (`.env`).
4.  It generates an ECDSA signature that is fully verifiable on-chain by the Payra smart contract.
5.  The resulting signature should be sent to the **frontend**, which must call `payOrder(...)` using the same parameters (`timestamp`, `orderId`, `amount`, `tokenAddress`, etc.) that were used to generate the signature.

---

### Checking On-Chain Order Status

You can verify whether a Payra order has been successfully paid on-chain:

```python
from payra_sdk import PayraOrderVerification, PayraSDKException

try:
    ORDER_ID = "ORDER-1753824905006-301-322"

    # Initialize verifier for a specific network
    verifier = PayraOrderVerification("polygon")

    print("\nChecking order status...")
    result = verifier.is_order_paid(ORDER_ID)

    print("Order ID:", ORDER_ID)
    print("Result:", result)

    if result["success"] and result["paid"]:
        print("Order is PAID on-chain")
    elif result["success"]:
        print("Order is NOT paid yet")
    else:
        print("Error:", result["error"])

except PayraSDKException as e:
    print(f"Payra SDK error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

#### Behind the Scenes

1.  The backend initializes a  `PayraOrderVerification`  object for the desired blockchain network.
3.  It calls  `is_order_paid(order_id)`  to check if the order transaction exists and is confirmed on-chain.
4.  The function returns a dictionary with:
    ```python
    {
	    "success": True,
	    "paid": True,
	    "error": None
	}
	```
5.  If  `paid`  is  `True`, the order has been successfully processed and confirmed by the Payra smart contract.

---

### Using Utility Functions

The `PayraUtils` module provides convenient helpers for token conversion, precision handling, and fiat currency operations.

```python
from payra_sdk import PayraUtils

# 🔹 Convert USD/token amount to smallest unit (Wei or token decimals)
amount_wei = PayraUtils.to_wei(3.34, 'polygon', 'usdt')
print("Amount in Wei:", amount_wei)  # 3340000

# 🔹 Convert from Wei back to readable token amount
amount = PayraUtils.from_wei(3340000, 'polygon', 'usdt', precision=2)
print("Readable amount:", amount)  # "3.34"

# 🔹 Get token decimals for any supported network
print("USDT decimals on Polygon:", PayraUtils.get_decimals("polygon", "usdt"))
print("POL decimals on Polygon:", PayraUtils.get_decimals("polygon", "pol"))

# 🔹 Convert fiat currency to USD using the built-in ExchangeRate API
usd_value = PayraUtils.convert_to_usd(100, "EUR")
print(f"100 EUR = {usd_value} USD")
```

#### Behind the Scenes

-   `to_wei(amount, network, token)`  – Converts a human-readable token amount into the smallest unit (used on-chain).
-   `from_wei(amount, network, token, precision)`  – Converts back from smallest unit to a formatted amount.
-   `get_decimals(network, token)`  – Returns the number of decimals for the given token on that network.
-   `convert_to_usd(amount, currency)`  – Converts fiat amounts (e.g. EUR, GBP) to USD using your ExchangeRate API key.

## Testing
You can run the included `examples` to test signing and verification:

```python
python3 example_signature.py
python3 example_order_verification.py
python3 example_utils.py
```

Make sure your (`.env`) file contains correct values for the `network` being used.

### Tips

- Always verify your  (`.env`)  configuration before running any signing or on-chain verification examples.
- The SDK examples are safe to run — they use  **read-only RPC calls**  (no real transactions are broadcast).
- You can modify  `example_signature.py`  to test custom token addresses or order parameters.

## Projects

-   [GitHub / Home](https://github.com/payracash)
-   [GitHub / Source](https://github.com/payracash/payra-sdk-python)
-   [GitHub / Issues](https://github.com/payracash/payra-sdk-python/issues)

## Project

-   [https://payra.cash](https://payra.cash)
-   [https://payra.tech](https://payra.tech)
-   [https://payra.xyz](https://payra.xyz)
-   [https://payra.eth](https://payra.eth)

## Social Media

- [Telegram Payra Group](https://t.me/+GhTyJJrd4SMyMDA0)
- [Telegram Announcements](https://t.me/payracash)
- [Twix (X)](https://x.com/PayraCash)
- [Hashnode](https://payra.hashnode.dev)

##  License

MIT © [Payra](https://github.com/payracash)
