from __future__ import annotations

from abc import ABC, abstractmethod
from ipaddress import IPv4Address, IPv6Address, ip_address
from typing import TYPE_CHECKING, Any, ClassVar

import requests
from polykit.text import print_color

from iplooker.api_key_manager import APIKeyManager

if TYPE_CHECKING:
    from iplooker.lookup_result import IPLookupResult


class IPLookupSource(ABC):
    """Abstract base class for IP lookup sources."""

    # Class variables that should be overridden by subclasses
    SOURCE_NAME: ClassVar[str]
    API_URL: ClassVar[str]
    TIMEOUT: ClassVar[int] = 5

    # Whether the source supports IPv6 addresses
    IPV6_SUPPORTED: ClassVar[bool] = True

    # Whether the source requires an API key
    REQUIRES_KEY: ClassVar[bool] = True
    REQUIRES_USER_KEY: ClassVar[bool] = False

    # How to send the API key (if needed)
    API_KEY_PARAM: ClassVar[str | None] = None  # For query params: ?key=value
    API_KEY_HEADER: ClassVar[str | None] = None  # For headers: {"Authorization": "Bearer {key}"}

    # Error response handling
    ERROR_KEYS: ClassVar[list[str]] = ["error"]  # Keys to check for error responses
    ERROR_MSG_KEYS: ClassVar[list[str]] = ["reason"]  # Keys for error messages in response
    SUCCESS_VALUES: ClassVar[dict[str, Any]] = {}  # Success values, e.g. {"status": 200}

    @classmethod
    def lookup(cls, ip: str) -> IPLookupResult | None:
        """Look up information about an IP address.

        Args:
            ip: The IP address to look up.

        Returns:
            A LookupResult object with the lookup results, or None if the lookup failed.
        """
        result, _ = cls.lookup_with_reason(ip)
        return result

    @classmethod
    def lookup_with_reason(cls, ip: str) -> tuple[IPLookupResult | None, str]:
        """Look up information about an IP address with failure reason.

        Args:
            ip: The IP address to look up.

        Returns:
            A tuple of (LookupResult or None, failure_reason).
        """
        ip_obj = cls._validate_ip(ip)
        if not ip_obj:
            return None, "invalid IP"

        # Check if this source supports IPv6
        if isinstance(ip_obj, IPv6Address) and not cls.IPV6_SUPPORTED:
            return None, "IPv6 not supported"

        # Get API key if required
        key = ""
        if cls.REQUIRES_KEY:
            key = APIKeyManager.get_key(cls.SOURCE_NAME, requires_user_key=cls.REQUIRES_USER_KEY)
            if not key:
                return None, ""  # Silently skip sources without keys

        # Prepare and make the request
        url, params, headers = cls._prepare_request(ip, key)
        data, error_reason = cls._make_request_with_reason(url, params=params, headers=headers)
        if not data:
            return None, error_reason

        # Check for errors in the response
        is_valid, error_reason = cls._is_response_valid_with_reason(data)
        if not is_valid:
            return None, error_reason

        try:
            result = cls._parse_response(data, ip_obj)
            return result, ""
        except Exception:
            return None, "parse error"

    @classmethod
    def _is_response_valid(cls, data: dict[str, Any]) -> bool:
        """Check if the response is valid (contains no errors and meets success criteria).

        Args:
            data: The response data to validate.

        Returns:
            True if the response is valid, False otherwise.
        """
        # Check for error response
        for error_key in cls.ERROR_KEYS:
            if data.get(error_key):
                # Try to get error message from various possible keys
                error_msg = "Unknown error"

                if hasattr(cls, "ERROR_MSG_KEYS") and cls.ERROR_MSG_KEYS:
                    for msg_key in cls.ERROR_MSG_KEYS:
                        if msg_value := data.get(msg_key):
                            error_msg = msg_value
                            break

                print(f"{cls.SOURCE_NAME} error: {error_msg}")
                return False

        # Check for specific success values
        for key, expected_value in cls.SUCCESS_VALUES.items():
            actual_value = data.get(key)
            if actual_value is not None and actual_value != expected_value:
                error_msg = f"{key} {actual_value} does not match required value {expected_value}"
                print(f"{cls.SOURCE_NAME} error: {error_msg}")
                return False

        return True

    @classmethod
    def _is_response_valid_with_reason(cls, data: dict[str, Any]) -> tuple[bool, str]:
        """Check if the response is valid (contains no errors and meets success criteria).

        Args:
            data: The response data to validate.

        Returns:
            A tuple of (is_valid, error_reason).
        """
        # Check for error response
        for error_key in cls.ERROR_KEYS:
            if data.get(error_key):
                # Try to get error message from various possible keys
                error_msg = "Unknown error"

                if hasattr(cls, "ERROR_MSG_KEYS") and cls.ERROR_MSG_KEYS:
                    for msg_key in cls.ERROR_MSG_KEYS:
                        if msg_value := data.get(msg_key):
                            error_msg = msg_value
                            break

                return False, error_msg

        # Check for specific success values
        for key, expected_value in cls.SUCCESS_VALUES.items():
            actual_value = data.get(key)
            if actual_value is not None and actual_value != expected_value:
                error_msg = f"{key} {actual_value} does not match required value {expected_value}"
                return False, error_msg

        return True, ""

    @classmethod
    def _prepare_request(cls, ip: str, key: str) -> tuple[str, dict[str, Any], dict[str, str]]:
        # Prepare request parameters
        url = cls.API_URL.format(ip=ip)
        params = {}
        headers = {}

        # Add API key to parameters or headers as configured
        if key:
            if cls.API_KEY_PARAM:
                params[cls.API_KEY_PARAM] = key
            if cls.API_KEY_HEADER:
                if f"{key}" in cls.API_KEY_HEADER:  # Format like "Bearer {key}"
                    headers["Authorization"] = cls.API_KEY_HEADER.format(key=key)
                else:  # Direct header value
                    headers[cls.API_KEY_HEADER] = key

        return url, params, headers

    @classmethod
    def _make_request(
        cls,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | None:
        """Make an HTTP request and return the JSON response.

        Args:
            url: The URL to request.
            params: Query parameters to include in the request.
            headers: HTTP headers to include in the request.

        Returns:
            The parsed JSON response as a dict, or None if the request failed.
        """
        try:
            response = requests.get(url, params=params, headers=headers, timeout=cls.TIMEOUT)

            if response.status_code == 429:
                print_color(
                    f" {cls.SOURCE_NAME} rate limit exceeded. Please try again later.", "yellow"
                )
                return None

            if response.status_code == 200:
                return response.json()

            print(f"{cls.SOURCE_NAME} API error: {response.status_code} - {response.text[:100]}")
            return None

        except requests.RequestException:
            print(f"Request error during {cls.SOURCE_NAME} lookup")
            return None
        except ValueError as e:
            print(f"JSON decode error during {cls.SOURCE_NAME} lookup: {e}")
            return None

    @classmethod
    def _make_request_with_reason(
        cls,
        url: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[dict[str, Any] | None, str]:
        """Make an HTTP request and return the JSON response.

        Args:
            url: The URL to request.
            params: Query parameters to include in the request.
            headers: HTTP headers to include in the request.

        Returns:
            A tuple of (parsed JSON response as a dict, error_reason).
        """
        try:
            response = requests.get(url, params=params, headers=headers, timeout=cls.TIMEOUT)

            if response.status_code == 429:
                return None, "rate limited"

            if response.status_code == 200:
                return response.json(), ""

            return None, f"API error: {response.status_code}"

        except requests.RequestException:
            return None, "request error"
        except ValueError:
            return None, "JSON decode error"

    @classmethod
    @abstractmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult | None:
        """Parse the response into a LookupResult."""
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @classmethod
    def _validate_ip(cls, ip: str) -> IPv4Address | IPv6Address | None:
        """Validate and convert an IP string to an IP address object.

        Args:
            ip: The IP address string to validate.

        Returns:
            An IPv4Address or IPv6Address object, or None if the IP is invalid.
        """
        try:
            return ip_address(ip)
        except ValueError:
            print(f"Invalid IP address: {ip}")
            return None

    @classmethod
    def get_env_var_name(cls) -> str:
        """Get the environment variable name for this source's API key."""
        return f"IPLOOKER_API_KEY_{cls.SOURCE_NAME.upper().replace('.', '')}"
