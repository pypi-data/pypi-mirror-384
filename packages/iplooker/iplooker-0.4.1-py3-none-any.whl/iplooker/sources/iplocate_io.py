from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPLocateLookup(IPLookupSource):
    """Perform IP lookups using the iplocate.io service."""

    SOURCE_NAME: ClassVar[str] = "iplocate.io"
    API_URL: ClassVar[str] = "https://iplocate.io/api/lookup/{ip}"
    API_KEY_PARAM: ClassVar[str | None] = "apiKey"
    ERROR_KEYS: ClassVar[list[str]] = ["error"]
    ERROR_MSG_KEYS: ClassVar[list[str]] = ["message"]

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the iplocate.io response into a LookupResult."""
        result = IPLookupResult(
            ip=ip_obj,
            source=cls.SOURCE_NAME,
            country=data.get("country"),
            region=data.get("subdivision"),
            city=data.get("city"),
        )

        # Extract organization information
        if (company := data.get("company", {})) and isinstance(company, dict):
            result.org = company.get("name")

        # Extract ASN information for ISP
        if (asn := data.get("asn", {})) and isinstance(asn, dict):
            result.isp = asn.get("name") or asn.get("domain")
            # If we don't have org info from company, use ASN data
            if not result.org:
                result.org = asn.get("name")

        return result
