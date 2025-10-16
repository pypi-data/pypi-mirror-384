from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPAPILookup(IPLookupSource):
    """Perform IP lookups using the IP-API.com service."""

    SOURCE_NAME: ClassVar[str] = "ip-api.com"
    API_URL: ClassVar[str] = "http://ip-api.com/json/{ip}"
    REQUIRES_KEY: ClassVar[bool] = False
    SUCCESS_VALUES: ClassVar[dict[str, Any]] = {"status": "success"}
    ERROR_MSG_KEYS: ClassVar[list[str]] = ["message"]

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult | None:
        """Parse the IP-API response into a LookupResult."""
        return IPLookupResult(
            ip=ip_obj,
            source=cls.SOURCE_NAME,
            country=data.get("country"),
            region=data.get("regionName"),
            city=data.get("city"),
            isp=data.get("isp"),
            org=data.get("org"),
        )
