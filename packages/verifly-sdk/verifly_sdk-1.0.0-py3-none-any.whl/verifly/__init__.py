"""
Verifly Python SDK - Inbound 2FA Verification System

Official Python client for Verifly API with HMAC-SHA256 authentication.

Example:
    from verifly import Verifly
    
    verifly = Verifly(
        api_key='your-api-key',
        secret_key='your-secret-key'
    )
    
    session = verifly.verification.create(
        phone='5551234567',
        methods=['sms', 'whatsapp']
    )
"""

__version__ = '1.0.0'
__author__ = 'SOCIFLY SOFTWARE LTD.'

from .client import Verifly
from .errors import (
    VeriflyError,
    AuthenticationError,
    ValidationError,
    InsufficientBalanceError,
    NotFoundError,
    RateLimitError,
    ServerError
)

__all__ = [
    'Verifly',
    'VeriflyError',
    'AuthenticationError',
    'ValidationError',
    'InsufficientBalanceError',
    'NotFoundError',
    'RateLimitError',
    'ServerError',
]
