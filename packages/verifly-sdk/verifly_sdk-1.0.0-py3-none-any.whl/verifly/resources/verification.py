"""
Verification Resource - Handle verification sessions
"""

from typing import Dict, List, Optional, Any
from ..utils.request import RequestHandler


class Verification:
    """Verification session management"""
    
    def __init__(self, request_handler: RequestHandler):
        """
        Initialize Verification resource
        
        Args:
            request_handler: Configured request handler
        """
        self.request = request_handler
    
    def create(
        self,
        phone: Optional[str] = None,
        email: Optional[str] = None,
        methods: Optional[List[str]] = None,
        recipient_contact: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create verification session
        
        Args:
            phone: Phone number (will be cleaned automatically)
            email: Email address
            methods: Allowed verification methods ['sms', 'whatsapp', 'call', 'email']
            recipient_contact: Contact for single-method flow
            metadata: Custom metadata
            
        Returns:
            Session data with sessionId and iframeUrl
            
        Example:
            session = verifly.verification.create(
                phone='5551234567',
                methods=['sms', 'whatsapp']
            )
        """
        data = {}
        
        if phone:
            data['phone'] = phone
        if email:
            data['email'] = email
        if methods:
            data['methods'] = methods
        if recipient_contact:
            data['recipientContact'] = recipient_contact
        if metadata:
            data['metadata'] = metadata
        
        response = self.request.post('/api/verify/create', data)
        return response.get('data', response)
    
    def get(self, session_id: str) -> Dict[str, Any]:
        """
        Get verification session status
        
        Args:
            session_id: Session ID
            
        Returns:
            Session status data
            
        Example:
            status = verifly.verification.get('session-id')
        """
        response = self.request.get(f'/api/verify/{session_id}')
        return response.get('data', response)
    
    def select_method(
        self,
        session_id: str,
        method: str,
        recipient_contact: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Select verification method
        
        Args:
            session_id: Session ID
            method: Selected method ('sms', 'whatsapp', 'call', 'email')
            recipient_contact: Contact if not provided in create
            
        Returns:
            Updated session data
            
        Example:
            session = verifly.verification.select_method(
                'session-id',
                method='sms',
                recipient_contact='5551234567'
            )
        """
        data = {'method': method}
        if recipient_contact:
            data['recipientContact'] = recipient_contact
        
        response = self.request.post(f'/api/verify/{session_id}/select-method', data)
        return response.get('data', response)
    
    def cancel(self, session_id: str) -> Dict[str, Any]:
        """
        Cancel verification session (temporary)
        
        Args:
            session_id: Session ID
            
        Returns:
            Cancellation result
            
        Example:
            result = verifly.verification.cancel('session-id')
        """
        response = self.request.post(f'/api/verify/{session_id}/cancel')
        return response
    
    def abort(self, session_id: str) -> Dict[str, Any]:
        """
        Abort verification session (permanent)
        
        Args:
            session_id: Session ID
            
        Returns:
            Abort result
            
        Example:
            result = verifly.verification.abort('session-id')
        """
        response = self.request.post(f'/api/verify/{session_id}/abort')
        return response
    
    def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance and recent transactions
        
        Returns:
            Balance data with recent transactions
            
        Example:
            balance = verifly.verification.get_balance()
            print(f"Balance: {balance['balance']} {balance['currency']}")
        """
        response = self.request.get('/api/verify/balance')
        return response.get('data', response)
