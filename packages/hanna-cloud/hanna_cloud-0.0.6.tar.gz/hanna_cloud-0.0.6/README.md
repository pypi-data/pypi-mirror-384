# HannaCloud Python Client
## NOT OFFICIALLY SUPPORTED BY HANNA --

A Python client library for interacting with the HannaCloud API.
This client provides methods for authentication and device data retrieval.
Developped solely for the HannaCloud HomeAssistant integration. At least for now.

## Installation
You can install the package using pip:

```bash
pip install hanna-cloud
```

## Usage

Here's a basic example of how to use the client:

```python
from hanna_cloud import HannaCloudClient

# Initialize the client
client = HannaCloudClient()

# Authenticate with your email and password
access_token = client.authenticate(email="your-email", password="your-password")
print(f"Access token: {access_token}")

# Get devices
devices = client.get_devices()
print(f"Devices: {devices}")

# Get user info
user_info = client.get_user()
print(f"User info: {user_info}")

# Get last device reading
last_reading = client.get_last_device_reading(device_id)
print(f"Last device reading: {last_reading}")

# Get device log history (example)
log_history = client.get_device_log_history(device_id=device_id)
print(f"Device log history: {log_history}")

# Disable Cl and pH pumps
client.set_remote_hold(device_id=device_id, setting=True)

# Enable Cl and pH pumps
client.set_remote_hold(device_id=device_id, setting=False)
```

## Error Handling

The client provides comprehensive error handling with specific exception classes:

### Exception Classes

- `HannaCloudError`: Base exception for all HannaCloud API errors
- `AuthenticationError`: Raised for authentication failures
- `DeviceNotFoundError`: Raised when a device is not found
- `APIError`: Raised for general API errors with status code and response data
- `RemoteHoldError`: Raised when remote hold operations fail
- `DeviceLogError`: Raised when device log operations fail
- `ValidationError`: Raised for input validation errors

### Example Error Handling

```python
from hanna_cloud.client import (
    HannaCloudClient, 
    AuthenticationError, 
    DeviceNotFoundError, 
    ValidationError
)

client = HannaCloudClient()

try:
    # This will raise AuthenticationError if not authenticated
    devices = client.get_devices()
except AuthenticationError as e:
    print(f"Authentication required: {e}")
    # Authenticate first
    client.authenticate("your-email", "your-password")
    devices = client.get_devices()

try:
    # This will raise ValidationError for empty device_id
    client.get_last_device_reading("")
except ValidationError as e:
    print(f"Validation error: {e}")

try:
    # This will raise DeviceNotFoundError if device doesn't exist
    readings = client.get_last_device_reading("nonexistent_device")
except DeviceNotFoundError as e:
    print(f"Device not found: {e}")
```

### Authentication

The client uses email and password authentication. Use the `authenticate` method to obtain and set the access token for subsequent requests.

### API Methods

- `authenticate(email: str, password: str, key_base64: str) -> str`: Authenticate and return access token
- `is_authenticated() -> bool`: Check if client is authenticated
- `get_devices() -> list`: Get list of user's devices
- `get_user() -> dict`: Get current user information
- `get_last_device_reading(device_id: str) -> list`: Get last reading for a device
- `get_device_log_history(device_id: str, from_dt: datetime, to_dt: datetime) -> list`: Get device log history
- `set_remote_hold(device_id: str, setting: bool) -> dict`: Set remote hold setting for a device

## License
This project is licensed under the MIT License - see the LICENSE file for details. 
