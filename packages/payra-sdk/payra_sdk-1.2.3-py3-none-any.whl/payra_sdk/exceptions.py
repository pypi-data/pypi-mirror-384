# payra-sdk-python/payra_sdk/exceptions.py

class PayraSDKException(Exception):
    """Base exception for Payra SDK errors."""
    pass

class InvalidArgumentError(PayraSDKException):
    """Raised when an invalid argument is provided."""
    pass

# NetworkError removed, as there's no network connection needed for signing
class SignatureError(PayraSDKException):
    """Raised when signature generation fails."""
    pass
