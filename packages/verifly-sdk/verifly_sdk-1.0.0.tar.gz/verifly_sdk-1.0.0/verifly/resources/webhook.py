"""
Webhook Resource - Verify webhook signatures
"""

import hashlib
import hmac
import json
from typing import Dict, Any, Optional


class Webhook:
    """Webhook signature verification"""
    
    def __init__(self, secret_key: str):
        """
        Initialize Webhook resource
        
        Args:
            secret_key: Application secret key
        """
        self.secret_key = secret_key
    
    def generate_signature(self, payload: Dict[str, Any], timestamp: str) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload
        
        Args:
            payload: Webhook payload
            timestamp: Timestamp from webhook
            
        Returns:
            HMAC signature in hexadecimal
            
        Example:
            signature = verifly.webhook.generate_signature(payload, timestamp)
        """
        payload_str = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)
        message = f"{payload_str}{timestamp}"
        
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return signature
    
    def verify(self, payload: Dict[str, Any], signature: str, timestamp: str) -> bool:
        """
        Verify webhook signature
        
        Args:
            payload: Webhook payload
            signature: Signature from X-Signature header
            timestamp: Timestamp from X-Timestamp header
            
        Returns:
            True if signature is valid
            
        Example:
            is_valid = verifly.webhook.verify(payload, signature, timestamp)
            if not is_valid:
                raise ValueError('Invalid signature')
        """
        expected_signature = self.generate_signature(payload, timestamp)
        return hmac.compare_digest(expected_signature, signature)
    
    def construct_event(
        self,
        payload: Dict[str, Any],
        signature: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """
        Verify webhook and construct event object
        
        Args:
            payload: Webhook payload
            signature: Signature from X-Signature header
            timestamp: Timestamp from X-Timestamp header
            
        Returns:
            Verified event data
            
        Raises:
            ValueError: If signature is invalid
            
        Example:
            event = verifly.webhook.construct_event(payload, signature, timestamp)
        """
        if not self.verify(payload, signature, timestamp):
            raise ValueError('Invalid webhook signature')
        
        return payload


class WebhookResponse:
    """Helper for creating webhook responses"""
    
    @staticmethod
    def success(message: str = 'OK') -> Dict[str, Any]:
        """
        Create success response
        
        Args:
            message: Success message
            
        Returns:
            Response dict
        """
        return {
            'success': True,
            'message': message
        }
    
    @staticmethod
    def error(message: str, status: int = 400) -> Dict[str, Any]:
        """
        Create error response
        
        Args:
            message: Error message
            status: HTTP status code
            
        Returns:
            Response dict with status
        """
        return {
            'success': False,
            'message': message,
            '_status': status
        }
    
    @staticmethod
    def unauthorized(message: str = 'Unauthorized') -> Dict[str, Any]:
        """
        Create unauthorized response
        
        Args:
            message: Error message
            
        Returns:
            Response dict with 401 status
        """
        return {
            'success': False,
            'message': message,
            '_status': 401
        }
