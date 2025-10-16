from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPAPIIsLookup(IPLookupSource):
    """Perform IP lookups using the ipapi.is service."""

    SOURCE_NAME: ClassVar[str] = "ipapi.is"
    API_URL: ClassVar[str] = "https://api.ipapi.is?ip={ip}"
    API_KEY_PARAM: ClassVar[str | None] = "key"

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the ipapi.is response into a LookupResult."""
        result = IPLookupResult(ip=ip_obj, source=cls.SOURCE_NAME)

        # Extract location data
        if location := data.get("location", {}):
            result.country = location.get("country")
            result.region = location.get("state")
            result.city = location.get("city")

        # Extract organization data
        if company := data.get("company", {}):
            result.org = company.get("name")

        # If no org was found in company, try asn
        if not result.org and (asn := data.get("asn", {})):
            result.org = asn.get("org")

        # Extract ISP information (datacenter info can serve as ISP)
        if datacenter := data.get("datacenter", {}):
            result.isp = datacenter.get("datacenter")
        elif not result.isp and (asn := data.get("asn", {})):
            result.isp = asn.get("domain")

        # Security information
        result.is_vpn = data.get("is_vpn")
        result.is_proxy = data.get("is_proxy")
        result.is_tor = data.get("is_tor")
        result.is_datacenter = data.get("is_datacenter")

        if (vpn := data.get("vpn", {})) and vpn.get("is_vpn") and vpn.get("service"):
            result.vpn_service = vpn.get("service")

        return result
