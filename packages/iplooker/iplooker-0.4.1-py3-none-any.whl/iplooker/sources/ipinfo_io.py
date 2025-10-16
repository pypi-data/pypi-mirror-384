from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPInfoLookup(IPLookupSource):
    """Perform IP lookups using the ipinfo.io service."""

    SOURCE_NAME: ClassVar[str] = "ipinfo.io"
    API_URL: ClassVar[str] = "https://ipinfo.io/{ip}/json"
    API_KEY_PARAM: ClassVar[str | None] = "token"
    ERROR_KEYS: ClassVar[list[str]] = ["error", "message"]

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the ipinfo.io response into a LookupResult."""
        result = IPLookupResult(
            ip=ip_obj,
            source=cls.SOURCE_NAME,
            country=data.get("country"),
            region=data.get("region"),
            city=data.get("city"),
        )

        # Extract organization information - in the standard API, org is directly provided
        if org := data.get("org"):
            # The org field often has format "AS#### Organization Name"
            if " " in org and len(org.split(" ", 1)) > 1:
                _, org_name = org.split(" ", 1)
                result.isp = org_name
                result.org = org_name
            else:
                result.org = org

        # Try company field if available
        if not result.org and (company := data.get("company")):
            if isinstance(company, dict):
                result.org = company.get("name")
            elif isinstance(company, str):
                result.org = company

        # Try ASN field if available
        if not result.isp and (asn := data.get("asn")):
            if isinstance(asn, dict):
                result.isp = asn.get("name") or asn.get("domain")
            elif isinstance(asn, str) and " " in asn:
                _, isp_name = asn.split(" ", 1)
                result.isp = isp_name

        # Security information
        if privacy := data.get("privacy", {}):
            result.is_vpn = privacy.get("vpn")
            result.is_proxy = privacy.get("proxy")
            result.is_tor = privacy.get("tor")
            result.is_datacenter = privacy.get("hosting")
            result.vpn_service = privacy.get("service") or None

        return result
