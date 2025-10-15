"""
Verifly Main Client
"""

from typing import Optional
from .utils.request import RequestHandler
from .resources.verification import Verification
from .resources.webhook import Webhook


class Verifly:
    """
    Main Verifly SDK client
    
    Example:
        from verifly import Verifly
        
        verifly = Verifly(
            api_key='your-api-key',
            secret_key='your-secret-key'
        )
        
        # Create verification session
        session = verifly.verification.create(
            phone='5551234567',
            methods=['sms', 'whatsapp']
        )
    """
    
    def __init__(
        self,
        api_key: str,
        secret_key: str,
        timeout: int = 30,
        debug: bool = False
    ):
        """
        Initialize Verifly client
        
        Args:
            api_key: Your Verifly API key
            secret_key: Application secret key (REQUIRED for HMAC authentication)
            timeout: Request timeout in seconds (default: 30)
            debug: Enable debug logging (default: False)
            
        Raises:
            ValueError: If api_key or secret_key is missing
            
        Example:
            # Required: Both API key and secret key
            verifly = Verifly(
                api_key='your-api-key',
                secret_key='your-secret-key'
            )
            
            # With additional options
            verifly = Verifly(
                api_key='your-api-key',
                secret_key='your-secret-key',
                timeout=60,
                debug=True
            )
        """
        if not api_key:
            raise ValueError('API key is required')
        
        if not secret_key:
            raise ValueError(
                'Secret key is required. '
                'Get it from Dashboard → Application → Secret Key'
            )
        
        self.api_key = api_key
        self.secret_key = secret_key
        self.timeout = timeout
        self.debug = debug
        
        # Initialize request handler
        self._request_handler = RequestHandler(
            api_key=self.api_key,
            secret_key=self.secret_key,
            timeout=self.timeout,
            debug=self.debug
        )
        
        # Initialize resources
        self.verification = Verification(self._request_handler)
        self.webhook = Webhook(self.secret_key)
    
    def set_secret_key(self, secret_key: str) -> None:
        """
        Update secret key
        
        Args:
            secret_key: New secret key
            
        Example:
            verifly.set_secret_key('new-secret-key')
        """
        self.secret_key = secret_key
        self.webhook = Webhook(secret_key)
        self._request_handler = RequestHandler(
            api_key=self.api_key,
            secret_key=secret_key,
            timeout=self.timeout,
            debug=self.debug
        )
        self.verification = Verification(self._request_handler)
    
    def set_debug(self, enabled: bool) -> None:
        """
        Enable or disable debug mode
        
        Args:
            enabled: Enable debug logging
            
        Example:
            verifly.set_debug(True)
        """
        self.debug = enabled
        self._request_handler = RequestHandler(
            api_key=self.api_key,
            secret_key=self.secret_key,
            timeout=self.timeout,
            debug=enabled
        )
        self.verification = Verification(self._request_handler)
