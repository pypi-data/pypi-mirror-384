from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPDataLookup(IPLookupSource):
    """Perform IP lookups using the ipdata.co service."""

    SOURCE_NAME: ClassVar[str] = "ipdata.co"
    API_URL: ClassVar[str] = "https://api.ipdata.co/{ip}"
    API_KEY_PARAM: ClassVar[str | None] = "api-key"
    ERROR_KEYS: ClassVar[list[str]] = ["error"]
    ERROR_MSG_KEYS: ClassVar[list[str]] = ["message"]

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the ipdata.co response into a LookupResult."""
        result = IPLookupResult(
            ip=ip_obj,
            source=cls.SOURCE_NAME,
            country=data.get("country_name"),
            region=data.get("region"),
            city=data.get("city"),
        )

        # Extract ASN information for ISP/org
        if asn_data := data.get("asn"):
            result.isp = asn_data.get("domain")
            result.org = asn_data.get("name")

        # Security information
        if threat := data.get("threat", {}):
            result.is_tor = threat.get("is_tor")
            result.is_proxy = threat.get("is_proxy")
            result.is_datacenter = threat.get("is_datacenter")
            result.is_anonymous = threat.get("is_anonymous")

        return result
