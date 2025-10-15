# Verifly Python SDK

Official Python SDK for [Verifly](https://www.verifly.net) - Inbound 2FA Verification System

[![PyPI version](https://img.shields.io/pypi/v/verifly-sdk.svg)](https://pypi.org/project/verifly-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/verifly-sdk.svg)](https://pypi.org/project/verifly-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **⚠️ Important:** This SDK uses **HMAC-SHA256 signature authentication**. Both API key and secret key are **required**. 

## Features

- ✅ **HMAC-SHA256 Authentication** - Secure API requests with cryptographic signatures
- ✅ **Multi-channel Verification** - SMS, WhatsApp, Email, Voice Call support
- ✅ **Webhook Verification** - Verify incoming webhook signatures
- ✅ **Type Hints** - Full type annotations for better IDE support
- ✅ **Error Handling** - Comprehensive error classes
- ✅ **Session Management** - Create, track, and manage verification sessions
- ✅ **Balance Inquiry** - Check account balance and transaction history

## Installation

```bash
pip install verifly-sdk
```

## Quick Start

```python
from verifly import Verifly

# Initialize client (BOTH keys required)
verifly = Verifly(
    api_key='your-api-key',
    secret_key='your-secret-key'
)

# Create verification session
session = verifly.verification.create(
    phone='5551234567',
    methods=['sms', 'whatsapp']
)

print(f"Session ID: {session['sessionId']}")
print(f"Iframe URL: {session['iframeUrl']}")
```

## Configuration

### Required Keys

| Key | Purpose | Required | How to Get |
|-----|---------|----------|------------|
| **API Key** | Identify your application | ✅ **REQUIRED** | Dashboard → Application → API Key |
| **Secret Key** | HMAC signature generation | ✅ **REQUIRED** | Dashboard → Application → Secret Key |

```python
from verifly import Verifly

# ✅ Basic configuration (both keys required)
verifly = Verifly(
    api_key='your-api-key',
    secret_key='your-secret-key'
)

# ✅ With additional options
verifly = Verifly(
    api_key='your-api-key',
    secret_key='your-secret-key',
    timeout=60,  # Request timeout in seconds
    debug=True   # Enable debug logging
)
```

## Usage

### Create Verification Session

```python
# Multi-method verification
session = verifly.verification.create(
    phone='5551234567',
    methods=['sms', 'whatsapp', 'call']
)

# Email verification
session = verifly.verification.create(
    email='user@example.com',
    methods=['email']
)

# Single-method (auto-send)
session = verifly.verification.create(
    phone='5551234567',
    methods=['sms'],
    recipient_contact='5551234567'
)
```

**Response:**
```python
{
    'sessionId': 'abc123...',
    'iframeUrl': 'https://www.verifly.net/verify/iframe/abc123...',
    'expiresAt': '2025-01-14T20:00:00.000Z',
    'allowedMethods': ['sms', 'whatsapp'],
    'method': None,  # or 'sms' if only one method
    'status': 'pending'
}
```

### Get Session Status

```python
status = verifly.verification.get('session-id')

if status['status'] == 'verified':
    print('Verification successful!')
    print(f"Verified at: {status['verifiedAt']}")
```

**Response:**
```python
{
    'sessionId': 'abc123...',
    'status': 'verified',
    'method': 'sms',
    'verificationCode': '123456',
    'recipientContact': '5551234567',
    'verifiedAt': '2025-01-14T19:55:00.000Z'
}
```

### Select Verification Method

If multiple methods are available, select one.

```python
verifly.verification.select_method(
    session_id='session-id',
    method='sms',
    recipient_contact='5551234567'  # If not provided in create
)
```

### Cancel Verification Session

Cancel an active verification session (user can retry later).

```python
verifly.verification.cancel('session-id')
```

### Abort Verification Session

Permanently abort a verification session (cannot be retried).

```python
verifly.verification.abort('session-id')
```

**Difference:**
- `cancel()` - Temporary cancellation, user can restart
- `abort()` - Permanent abort, session is completely terminated

### Get Balance

Get account balance and recent transactions.

```python
balance = verifly.verification.get_balance()

print(f"Balance: {balance['balance']} {balance['currency']}")
print(f"Recent transactions: {balance['recentTransactions']}")
```

**Response:**
```python
{
    'balance': 1500.00,
    'currency': 'TRY',
    'userId': '...',
    'email': 'user@example.com',
    'recentTransactions': [
        {
            'type': 'credit',
            'amount': 500,
            'description': 'Balance added',
            'createdAt': '2025-01-14T...'
        }
        # ... more transactions
    ]
}
```

## Webhooks

### Verify Webhook Signature

Verify that a webhook request actually came from Verifly.

```python
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/verifly', methods=['POST'])
def verifly_webhook():
    # Get headers
    signature = request.headers.get('X-Signature')
    timestamp = request.headers.get('X-Timestamp')
    
    # Get payload
    payload = request.get_json()
    
    # Verify signature
    is_valid = verifly.webhook.verify(payload, signature, timestamp)
    
    if not is_valid:
        return jsonify({'error': 'Invalid signature'}), 401
    
    # Process webhook
    if payload['event'] == 'verification.completed':
        session_id = payload['data']['sessionId']
        print(f"Verification completed: {session_id}")
    
    return jsonify({'success': True})
```

### Construct Event (Auto-verify)

```python
try:
    event = verifly.webhook.construct_event(payload, signature, timestamp)
    # Event is verified, safe to use
    print(f"Event type: {event['event']}")
except ValueError as e:
    print(f"Invalid webhook: {e}")
```

## Error Handling

The SDK uses exceptions for error handling (standard Python practice).

### Try-Except Pattern

```python
from verifly import Verifly, AuthenticationError, InsufficientBalanceError, ValidationError

try:
    session = verifly.verification.create(
        phone='5551234567',
        methods=['sms']
    )
    
    print('✅ Success:', session)
    
except AuthenticationError as e:
    print(f'❌ Authentication failed: {e}')
    # Check your API key and secret key
    
except InsufficientBalanceError as e:
    print(f'❌ Insufficient balance: {e}')
    print(f'Balance data: {e.balance_data}')
    # User needs to add balance
    
except ValidationError as e:
    print(f'❌ Validation error: {e}')
    # Fix input parameters
    
except Exception as e:
    print(f'❌ Unknown error: {e}')
```

### Error Types

| Error Class | HTTP Status | Description |
|------------|-------------|-------------|
| `AuthenticationError` | 401 | Invalid API key or secret key |
| `ValidationError` | 400 | Invalid request parameters |
| `InsufficientBalanceError` | 402 | Not enough account balance |
| `NotFoundError` | 404 | Session or resource not found |
| `RateLimitError` | 429 | Too many requests |
| `ServerError` | 500 | Server error |

### Helper Function (Optional)

If you prefer `{'success': bool, 'error': str}` format:

```python
def safe_verify(phone):
    try:
        session = verifly.verification.create(
            phone=phone,
            methods=['sms', 'whatsapp']
        )
        return {'success': True, 'data': session}
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }

# Usage
result = safe_verify('5551234567')
if result['success']:
    print('✅', result['data'])
else:
    print('❌', result['error'])
```

## Framework Integration

### Flask

```python
from flask import Flask, request, jsonify
from verifly import Verifly

app = Flask(__name__)
verifly = Verifly(api_key='...', secret_key='...')

@app.route('/verify/create', methods=['POST'])
def create_verification():
    try:
        data = request.get_json()
        session = verifly.verification.create(
            phone=data.get('phone'),
            methods=['sms', 'whatsapp']
        )
        return jsonify({'success': True, 'data': session})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
```

### Django

```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from verifly import Verifly
import json

verifly = Verifly(api_key='...', secret_key='...')

@csrf_exempt
def create_verification(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            session = verifly.verification.create(
                phone=data.get('phone'),
                methods=['sms', 'whatsapp']
            )
            return JsonResponse({'success': True, 'data': session})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
```

### FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from verifly import Verifly

app = FastAPI()
verifly = Verifly(api_key='...', secret_key='...')

class VerifyRequest(BaseModel):
    phone: str
    methods: list[str] = ['sms', 'whatsapp']

@app.post('/verify/create')
async def create_verification(request: VerifyRequest):
    try:
        session = verifly.verification.create(
            phone=request.phone,
            methods=request.methods
        )
        return {'success': True, 'data': session}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## API Reference

### Verifly

#### Constructor

```python
Verifly(api_key, secret_key, timeout=30, debug=False)
```

#### Methods

- `set_secret_key(secret_key)` - Update secret key
- `set_debug(enabled)` - Enable/disable debug mode

### Verification

#### Methods

- `create(phone=None, email=None, methods=None, recipient_contact=None, metadata=None)` - Create verification session
- `get(session_id)` - Get session status
- `select_method(session_id, method, recipient_contact=None)` - Select verification method
- `cancel(session_id)` - Cancel session (temporary)
- `abort(session_id)` - Abort session (permanent)
- `get_balance()` - Get account balance and transactions

### Webhook

#### Methods

- `verify(payload, signature, timestamp)` - Verify webhook signature
- `generate_signature(payload, timestamp)` - Generate signature (for testing)
- `construct_event(payload, signature, timestamp)` - Construct verified event object

## Support

- 📧 Email: info@verifly.net
- 🌐 Website: https://www.verifly.net
- 📚 Documentation: https://www.verifly.net/docs
- 🐛 Issues: https://github.com/tlgsn/verifly-python-sdk/issues

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

**Made with ❤️ by SOCIFLY SOFTWARE LTD.**
