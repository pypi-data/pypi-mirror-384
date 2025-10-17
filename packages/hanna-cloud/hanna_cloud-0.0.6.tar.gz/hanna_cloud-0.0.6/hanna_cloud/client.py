import base64
import random
import requests
import string
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from datetime import datetime
import logging
import time

# This key is NOT private. It is found in the JavaScript code of the Hanna Cloud webapp at https://www.hannacloud.com
DEFAULT_ENCRYPTION_KEY = "MzJmODBmMDU0ZTAyNDFjYWM0YTVhOGQxY2ZlZTkwMDM="


class HannaCloudClient:
    """Client for interacting with the HannaCloud API."""

    def __init__(self):
        """
        Initialize the HannaCloud API client.
        """
        self.base_url = "https://www.hannacloud.com/api"
        self.key_base64 = DEFAULT_ENCRYPTION_KEY
        self.headers = {'Accept': '*/*',
                        'content-type': 'application/json'}
        self.access_token = None
        self.email = None
        self.password = None
        logging.basicConfig(level=logging.INFO)

    def _make_request(self, method, endpoint, **kwargs):
        """
        Internal method to make HTTP requests to the HannaCloud API.
        Args:
            method (str): HTTP method (e.g., 'POST').
            endpoint (str): API endpoint.
            **kwargs: Additional arguments for requests.request.
        Returns:
            dict: The 'data' field from the API response,
                  or an empty dict if not present.
                  If the response is not JSON, it will be returned as is.
        Raises:
            requests.HTTPError: If the HTTP request fails.
        """
        def _execute_request():
            self.headers['authorization'] = f"Bearer {self.access_token}"
            headers = {**self.headers, **kwargs.get('headers', {})}
            url = f'{self.base_url}/{endpoint}'
            return requests.request(method=method, url=url, headers=headers, **kwargs)

        response = _execute_request()
        logging.debug(f"{method} {self.base_url}/{endpoint} {response.status_code}")

        if response.status_code == 403:
            logging.info("Authentication failed: 403. Re-authenticating.")
            self.authenticate(self.email, self.password, self.key_base64)
            response = _execute_request()

        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            if response.status_code == 404:
                raise DeviceNotFoundError(f"Resource not found: {endpoint}") from e
            elif response.status_code == 401:
                raise AuthenticationError("Invalid credentials or token expired") from e
            elif response.status_code == 403:
                raise AuthenticationError("Access forbidden - insufficient permissions") from e
            elif response.status_code >= 500:
                raise APIError(f"Server error: {response.status_code}", response.status_code) from e
            else:
                raise APIError(f"HTTP {response.status_code}: {e}", response.status_code) from e

        try:
            return response.json().get('data', {})
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}", response_data=response.text) from e

    def hanna_encrypt(self, plaintext: str) -> str:
        """
        Encrypts the given plaintext using AES CBC mode
        with a random IV and a base64-encoded key.
        Args:
            plaintext (str): The text to encrypt.
        Returns:
            str: The IV and the encrypted data (as hex), separated by a colon.
        """
        # Decode the base64-encoded key to bytes
        key = base64.b64decode(self.key_base64)
        # Generate a random IV
        choices = string.ascii_letters + string.digits
        iv = ''.join(random.choice(choices) for _ in range(16)).encode()
        # Create a new AES cipher with the key and IV
        cipher = AES.new(key, AES.MODE_CBC, iv)
        # Pad the plaintext to the block size
        padded = pad(plaintext.encode(), AES.block_size)
        # Encrypt the padded plaintext
        encrypted = cipher.encrypt(padded)
        # Return the IV and the encrypted data (as hex), separated by a colon
        return f"{iv.decode()}:{encrypted.hex()}"

    def authenticate(self, email: str, password: str) \
            -> tuple[str, str]:
        """
        Authenticates the user with the given email and password.
        Args:
            email (str): The user's email address.
            password (str): The user's password.
            key_base64 (str): The base64-encoded key.
        Returns:
            Tuple[str, str]: The access token and refresh token.
        Raises:
            ValueError: If authentication fails or tokens are missing.
        """
        self.email = email
        self.password = password
        json_data = {
            'operationName': 'Login',
            'variables': {
                'email': self.hanna_encrypt(email),
                'password': self.hanna_encrypt(password),
                'userLanguage': 'English',
                'source': 'web',
            },
            'query': (
                """
                query Login($email: String!, $password: String!,
                            $userLanguage: String!, $source: String) {
                  login(
                    email: $email
                    password: $password
                    language: $userLanguage
                    source: $source
                  ) {
                    token
                    tokenType
                  }
                }
                """
            ),
        }
        max_retries, retry_delay, retries = 3, 1, 0
        while retries < max_retries:
            response = self._make_request('POST', 'auth', json=json_data)
            if response.get("login", {}):
                break
            retries += 1
            time.sleep(retry_delay)
        if not response.get("login", {}):
            raise AuthenticationError("Authentication failed: 'login' key missing in response.")

        for token in response['login']:
            if token.get('tokenType') == 'accessToken':
                self.access_token = token.get('token')
        return self.access_token

    def is_authenticated(self) -> bool:
        """
        Check if the client is authenticated.
        Returns:
            bool: True if authenticated, False otherwise.
        """
        return self.access_token is not None

    def _require_authentication(self):
        """
        Require authentication for protected operations.
        Raises:
            AuthenticationError: If not authenticated.
        """
        if not self.is_authenticated():
            raise AuthenticationError("Authentication required. Call authenticate() first.")

    def get_last_device_reading(self, device_id: str):
        """
        Retrieves the last reading for the specified device(s).
        Args:
            device_id (str): The device ID to get readings for.
        Returns:
            list: Last device readings.
        Raises:
            DeviceNotFoundError: If no readings are found for the device.
        """
        self._require_authentication()
        if not device_id:
            raise ValidationError("device_id cannot be empty")
        json_data = {
            'operationName': 'GetLastDeviceReading',
            'variables': {'deviceIds': [device_id]},
            'query': (
                """
                query GetLastDeviceReading($deviceIds: [String!]) {
                  lastDeviceReadings(deviceIds: $deviceIds) {
                    DID
                    DT
                    messages
                  }
                }
                """
            )
        }
        response = self._make_request('POST', 'graphql', json=json_data)
        readings = response.get('lastDeviceReadings', [[]])[0]
        if not readings:
            raise DeviceNotFoundError(f"No readings found for device {device_id}")

        self.reading = readings
        self.alarms = readings.get('messages', {}).get('alarms', [])
        self.warnings = readings.get('messages', {}).get('warnings', [])
        self.errors = readings.get('messages', {}).get('errors', [])
        self.status = readings.get('messages', {}).get('status', {})
        self.parameters = readings.get('messages', {}).get('parameters', {})
        return readings

    def get_devices(self):
        """
        Retrieves a list of devices for the user.
        Returns:
            dict: Device information.
        """
        self._require_authentication()
        json_data = {
            "operationName": "Devices",
            "variables": {
                "modelGroups": [
                    "BL12x", "BL13x", "BL13xs"
                ],
                "deviceLogs": True
            },
            "query": (
                """
                query Devices($modelGroups: [String!], $deviceLogs: Boolean!) {
                  devices(modelGroups: $modelGroups, deviceLogs: $deviceLogs) {
                    _id
                    DID
                    DM
                    modelGroup
                    DT
                    DINFO {
                      deviceName
                      deviceVersion
                      userId
                      emailId
                      assignedUsers {
                        emailId
                        __typename
                      }
                      tankId
                      tankName
                      __typename
                    }
                    parentId
                    childDevices {
                      DID
                      __typename
                    }
                    dashboardViewStatus
                    deviceOrder
                    secondaryUser
                    reportedSettings
                    status
                    lastUpdated
                    message
                    deviceName
                    batteryStatus
                    __typename
                  }
                }
                """
            )
        }
        response = self._make_request('POST', 'graphql', json=json_data)
        devices = response.get('devices', [])
        for device in devices:
            sy = device.get("reportedSettings", {}).get("SY")
            device['manufacturer'] = sy.split(",")[0]
            device['name'] = f"{device.get('DINFO', {}).get('deviceName')}"
            device['serial_number'] = sy.split(",")[4]
            device['sw_version'] = "".join(sy.split(",")[2:4]).replace("&#47;", "/")
        return devices

    def get_user(self):
        """
        Retrieves information about the current user.
        Returns:
            dict: User information.
        """
        self._require_authentication()
        json_data = {
            "operationName": "getUser",
            "variables": {},
            "query": (
                """
                query getUser {
                  currentUser {
                    _id
                    fName
                    lName
                    regDate
                    emailId
                    notificationSetting
                    aesObjectId
                    lang
                    tempUnit
                    timeFormat
                    dateFormat
                    dashboardView
                    blDeviceSorting
                    __typename
                  }
                }
                """
            )
        }
        response = self._make_request('POST', 'graphql', json=json_data)
        return response.get('currentUser', {})

    def get_device_log_history(self,
                               device_id: str,
                               from_dt: datetime = None,
                               to_dt: datetime = None):
        """
        Retrieves the device log history for a given device and date range.
        Args:
            device_id (str): The device ID.
            from_dt (datetime): Start date for log history.
            to_dt (datetime): End date for log history.
        Returns:
            list: Device log history data.
        Raises:
            DeviceLogError: If no device log history is found.
        """
        self._require_authentication()
        if not device_id:
            raise ValidationError("device_id cannot be empty")
        if from_dt and to_dt and from_dt > to_dt:
            raise ValidationError("from_dt cannot be later than to_dt")
        from_dt = from_dt or datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        to_dt = to_dt or datetime.now()

        json_data = {
            "operationName": "deviceLogHistory",
            "variables": {
                "deviceId": device_id,
                "from": from_dt.isoformat(),
                "to": to_dt.isoformat(),
                "count": 10000
            },
            "query": (
                """
                query deviceLogHistory($deviceId: String!,
                                       $from: String!,
                                       $to: String!) {
                  deviceLogHistory(deviceId: $deviceId, from: $from, to: $to) {
                    data
                    endDate
                    startDate
                    parameterNames
                    __typename
                  }
                }
                """
            )
        }
        response = self._make_request('POST', 'graphql', json=json_data)
        device_log_history = response.get('deviceLogHistory', [])
        if not device_log_history:
            raise DeviceLogError(f"No device log history found for device {device_id}")
        return device_log_history

    def set_remote_hold(self, device_id: str, setting: bool):
        """
        Sets the remote hold (disable pumps) setting for a device.
        Args:
            device_id (str): The device ID.
            setting (bool): The remote hold setting.
        Raises:
            RemoteHoldError: If the remote hold operation fails.
        """
        self._require_authentication()
        if not device_id:
            raise ValidationError("device_id cannot be empty")
        if not isinstance(setting, bool):
            raise ValidationError("setting must be a boolean value")
        json_data = {
            "operationName": "RemoteHold",
            "variables": {"deviceId": device_id, "remoteHold": setting},
            "query": (
                """
                mutation RemoteHold($deviceId: String!, $remoteHold: Boolean!) {
                  deviceRemoteHold(deviceId: $deviceId, remoteHold: $remoteHold) {
                    data
                    __typename
                  }
                }
                """
            )
        }
        response = self._make_request('POST', 'graphql', json=json_data)
        if response.get('deviceRemoteHold', {}).get('data', {}).get('message') != 'remoteHoldSuccess':
            raise RemoteHoldError("Remote hold operation failed. Check device status and permissions.")
        return response.get('deviceRemoteHold', {})


class HannaCloudError(Exception):
    """Base exception for HannaCloud API errors."""
    pass


class AuthenticationError(HannaCloudError):
    """Exception raised for authentication errors."""
    pass


class DeviceNotFoundError(HannaCloudError):
    """Exception raised when a device is not found."""
    pass


class APIError(HannaCloudError):
    """Exception raised for general API errors."""
    def __init__(self, message, status_code=None, response_data=None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RemoteHoldError(HannaCloudError):
    """Exception raised when remote hold operation fails."""
    pass


class DeviceLogError(HannaCloudError):
    """Exception raised when device log operations fail."""
    pass


class ValidationError(HannaCloudError):
    """Exception raised for validation errors."""
    pass
