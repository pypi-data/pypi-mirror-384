"""
HTTP Request Handler with HMAC-SHA256 Authentication
"""

import hashlib
import hmac
import time
from typing import Dict, Any, Optional
import requests

from ..errors import (
    VeriflyError,
    AuthenticationError,
    ValidationError,
    InsufficientBalanceError,
    NotFoundError,
    RateLimitError,
    ServerError
)


class RequestHandler:
    """Handles HTTP requests with HMAC-SHA256 authentication"""
    
    def __init__(self, api_key: str, secret_key: str, timeout: int = 30, debug: bool = False):
        """
        Initialize request handler
        
        Args:
            api_key: Verifly API key
            secret_key: Application secret key for HMAC signature
            timeout: Request timeout in seconds
            debug: Enable debug logging
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = 'https://www.verifly.net'
        self.timeout = timeout
        self.debug = debug
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Verifly-Python-SDK/1.0.0'
        })
    
    def _generate_signature(self, payload: str, timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature
        
        Args:
            payload: Request payload as JSON string
            timestamp: Current timestamp
            
        Returns:
            HMAC signature in hexadecimal
        """
        message = f"{payload}{timestamp}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        if self.debug:
            print(f"[Verifly Debug] Generating signature:")
            print(f"  Payload: {payload}")
            print(f"  Timestamp: {timestamp}")
            print(f"  Message: {message}")
            print(f"  Signature: {signature}")
        
        return signature
    
    def _get_headers(self, payload: str) -> Dict[str, str]:
        """
        Generate request headers with HMAC signature
        
        Args:
            payload: Request payload as JSON string
            
        Returns:
            Headers dict with authentication
        """
        timestamp = str(int(time.time()))
        signature = self._generate_signature(payload, timestamp)
        
        return {
            'X-API-Key': self.api_key,
            'X-Signature': signature,
            'X-Timestamp': timestamp
        }
    
    def _handle_error(self, response: requests.Response) -> VeriflyError:
        """
        Convert HTTP error to appropriate exception
        
        Args:
            response: HTTP response object
            
        Returns:
            Appropriate VeriflyError subclass
        """
        try:
            data = response.json()
        except:
            data = {}
        
        message = data.get('message') or data.get('error') or 'Unknown error'
        status = response.status_code
        
        error_map = {
            400: ValidationError,
            401: AuthenticationError,
            402: InsufficientBalanceError,
            404: NotFoundError,
            429: RateLimitError,
            500: ServerError,
            502: ServerError,
            503: ServerError
        }
        
        error_class = error_map.get(status, VeriflyError)
        return error_class(message, status, data)
    
    def request(
        self,
        method: str,
        path: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated HTTP request
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API endpoint path
            data: Request body data
            params: URL query parameters
            
        Returns:
            Response data as dict
            
        Raises:
            VeriflyError: On API errors
        """
        url = f"{self.base_url}{path}"
        
        # Prepare payload
        import json
        payload = json.dumps(data or {}, separators=(',', ':'))
        
        # Generate headers with signature
        headers = self._get_headers(payload)
        
        if self.debug:
            print(f"[Verifly Debug] Request:")
            print(f"  Method: {method}")
            print(f"  URL: {url}")
            print(f"  Headers: {headers}")
            print(f"  Data: {data}")
            print(f"  Params: {params}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            
            if self.debug:
                print(f"[Verifly Debug] Response:")
                print(f"  Status: {response.status_code}")
                print(f"  Body: {response.text}")
            
            # Check for errors
            if not response.ok:
                raise self._handle_error(response)
            
            return response.json()
            
        except requests.RequestException as e:
            if isinstance(e, requests.Timeout):
                raise VeriflyError(f"Request timeout after {self.timeout}s")
            raise VeriflyError(str(e))
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request"""
        return self.request('GET', path, params=params)
    
    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make POST request"""
        return self.request('POST', path, data=data)
    
    def put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make PUT request"""
        return self.request('PUT', path, data=data)
    
    def delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request"""
        return self.request('DELETE', path)
