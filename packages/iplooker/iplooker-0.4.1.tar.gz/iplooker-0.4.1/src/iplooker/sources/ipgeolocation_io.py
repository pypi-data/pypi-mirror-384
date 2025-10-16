from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPGeolocationLookup(IPLookupSource):
    """Perform IP lookups using the ipgeolocation.io service."""

    SOURCE_NAME: ClassVar[str] = "ipgeolocation.io"
    API_URL: ClassVar[str] = "https://api.ipgeolocation.io/v2/ipgeo"
    API_KEY_PARAM: ClassVar[str | None] = "apiKey"
    ERROR_KEYS: ClassVar[list[str]] = ["status"]
    ERROR_MSG_KEYS: ClassVar[list[str]] = ["message"]
    SUCCESS_VALUES: ClassVar[dict[str, Any]] = {"status": 200}

    @classmethod
    def _prepare_request(cls, ip: str, key: str) -> tuple[str, dict[str, Any], dict[str, str]]:
        """Prepare request for ipgeolocation.io API which expects IP as a query parameter."""
        url = cls.API_URL
        params = {"ip": ip}
        headers = {}

        # Add API key to parameters if provided
        if key and cls.API_KEY_PARAM:
            params[cls.API_KEY_PARAM] = key

        return url, params, headers

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the ipgeolocation.io response into a LookupResult."""
        result = IPLookupResult(ip=ip_obj, source=cls.SOURCE_NAME)

        # Extract location information
        if location := data.get("location", {}):
            result.country = location.get("country_name")
            result.region = location.get("state_prov")
            result.city = location.get("city")

        return result
