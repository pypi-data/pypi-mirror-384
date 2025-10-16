from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from iplooker.lookup_result import IPLookupResult
from iplooker.lookup_source import IPLookupSource

if TYPE_CHECKING:
    from ipaddress import IPv4Address, IPv6Address


class IPRegistryLookup(IPLookupSource):
    """Perform IP lookups using the IPRegistry API."""

    SOURCE_NAME: ClassVar[str] = "ipregistry.co"
    API_URL: ClassVar[str] = "https://api.ipregistry.co/{ip}"
    REQUIRES_USER_KEY: ClassVar[bool] = True
    API_KEY_PARAM: ClassVar[str | None] = "key"

    @classmethod
    def _parse_response(
        cls, data: dict[str, Any], ip_obj: IPv4Address | IPv6Address
    ) -> IPLookupResult:
        """Parse the IPRegistry API response into a LookupResult."""
        # Handle the case where the response has a 'results' array
        if "results" in data and isinstance(data["results"], list) and data["results"]:
            data = data["results"][0]

        result = IPLookupResult(ip=ip_obj, source=cls.SOURCE_NAME)

        # Extract location data
        if location := data.get("location", {}):
            if country := location.get("country", {}):
                result.country = country.get("name")

            if region := location.get("region", {}):
                result.region = region.get("name")

            result.city = location.get("city")

        # Extract organization/ISP data
        if connection := data.get("connection", {}):
            result.isp = connection.get("domain")
            result.org = connection.get("organization")
        elif company := data.get("company", {}):
            result.org = company.get("name")

        # Extract security information
        if security := data.get("security", {}):
            result.is_vpn = security.get("is_vpn")
            result.is_proxy = security.get("is_proxy")
            result.is_tor = security.get("is_tor")
            result.is_datacenter = security.get("is_cloud_provider")
            result.is_anonymous = security.get("is_anonymous")

        return result
