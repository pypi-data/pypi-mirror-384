from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPAPICoLookup(IPLookupSource):
    """Perform IP lookups using the ipapi.co service."""

    SOURCE_NAME: ClassVar[str] = "ipapi.co"
    API_URL: ClassVar[str] = "https://ipapi.co/{ip}/json/"
    REQUIRES_KEY: ClassVar[bool] = False

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the ipapi.co response into a LookupResult."""
        return IPLookupResult(
            ip=ip_obj,
            source=cls.SOURCE_NAME,
            country=data.get("country_name"),
            region=data.get("region"),
            city=data.get("city"),
            isp=None,  # ipapi.co doesn't provide ISP information
            org=data.get("org"),
        )
