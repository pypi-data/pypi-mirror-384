"""
Verifly SDK Error Classes
"""

class VeriflyError(Exception):
    """Base exception for all Verifly errors"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response
    
    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(VeriflyError):
    """Raised when authentication fails (401)"""
    pass


class ValidationError(VeriflyError):
    """Raised when request validation fails (400)"""
    pass


class InsufficientBalanceError(VeriflyError):
    """Raised when account has insufficient balance (402)"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message, status_code, response)
        self.balance_data = response.get('data') if response else None


class NotFoundError(VeriflyError):
    """Raised when resource is not found (404)"""
    pass


class RateLimitError(VeriflyError):
    """Raised when rate limit is exceeded (429)"""
    pass


class ServerError(VeriflyError):
    """Raised when server error occurs (500+)"""
    pass
