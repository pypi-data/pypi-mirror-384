"""Does an IP lookup using multiple sources.

This script is designed to do an IP lookup using multiple sources. It can be used to get
more information about an IP address, including the country, region, city, ISP, and
organization. It collates the information and combines sources that say the same thing.
"""

from __future__ import annotations

from ipaddress import ip_address as parse_ip_address
from typing import TYPE_CHECKING, ClassVar

import requests
from polykit import PolyArgs, PolyEnv
from polykit.cli import halo_progress, handle_interrupt
from polykit.core import polykit_setup
from polykit.text import color, print_color

from iplooker.ip_formatter import IPFormatter
from iplooker.sources import (
    IPAPICoLookup,
    IPAPIIsLookup,
    IPAPILookup,
    IPDataLookup,
    IPGeolocationLookup,
    IPInfoLookup,
    IPLocateLookup,
    IPRegistryLookup,
)

if TYPE_CHECKING:
    import argparse

    from iplooker.lookup_result import IPLookupResult
    from iplooker.lookup_source import IPLookupSource

polykit_setup()

env = PolyEnv()


class IPLooker:
    """Perform an IP lookup using multiple sources."""

    TIMEOUT: ClassVar[int] = 5

    # List of lookup sources to use
    LOOKUP_SOURCES: ClassVar[list[type[IPLookupSource]]] = [
        IPAPICoLookup,
        IPAPIIsLookup,
        IPAPILookup,
        IPDataLookup,
        IPGeolocationLookup,
        IPInfoLookup,
        IPLocateLookup,
        IPRegistryLookup,
    ]

    def __init__(self, ip_address: str, do_lookup: bool = True):
        try:
            self.ip_address: str = ip_address
            self.ip_obj = parse_ip_address(ip_address)
            self.formatter: IPFormatter = IPFormatter(ip_address)
            self.missing_sources: dict[str, str] = {}  # source_name -> failure_reason
            self.results: list[IPLookupResult] = []

            if do_lookup:
                self.perform_ip_lookup()
        except ValueError:
            print_color(f"Invalid IP address: {ip_address}", "red")
            raise

    def perform_ip_lookup(self) -> None:
        """Fetch IP data from all sources."""
        with halo_progress(
            start_message=f"Getting results for {self.ip_address}",
            end_message=None,
            fail_message=f"Failed to get results for {self.ip_address}",
        ) as spinner:
            for source_class in self.LOOKUP_SOURCES:
                if spinner:
                    spinner.text = color(f"Querying {source_class.SOURCE_NAME}...", "cyan")

                result, failure_reason = source_class.lookup_with_reason(self.ip_address)
                if result:
                    self.results.append(result)
                elif failure_reason:  # Only track if there's an actual error reason
                    self.missing_sources[source_class.SOURCE_NAME] = failure_reason

        self.display_results()

    def display_results(self) -> None:
        """Display the consolidated results and any sources with no data."""
        if not self.results:
            print_color(
                "\n⚠️  WARNING: No sources returned results. Check your API keys and internet connection.",
                "yellow",
            )
            return

        formatted_results = []
        for result in self.results:
            formatted = self.formatter.format_lookup_result(result)
            formatted_results.append(formatted)

        print_color(f"\n{color(f'Results for {self.ip_address}:', 'cyan')}", "blue")
        self.formatter.print_consolidated_results(formatted_results)

        if self.missing_sources:
            missing_list = [
                f"{source} ({reason})" for source, reason in self.missing_sources.items()
            ]
            print_color(f"\nNo data from: {', '.join(missing_list)}", "blue")

    @staticmethod
    def get_external_ip() -> str | None:
        """Get the external IP address using ipify.org."""
        try:
            response = requests.get("https://api.ipify.org", timeout=IPLooker.TIMEOUT)
            if response.status_code == 200:
                external_ip = response.text
                print_color(f"Your external IP address is: {external_ip}", "blue")
                return external_ip
        except requests.exceptions.RequestException as e:
            print_color(f"Failed to get external IP: {e}", "red")
        return None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = PolyArgs(description=__doc__, lines=2)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("ip_address", type=str, nargs="?", help="the IP address to look up")
    group.add_argument("-m", "--me", action="store_true", help="get your external IP address")
    group.add_argument("-l", "--lookup", action="store_true", help="get lookup for your IP address")
    return parser.parse_args()


@handle_interrupt()
def main() -> None:
    """Main function."""
    args = parse_args()
    if args.lookup:
        args.me = True

    if args.me:
        ip_address = IPLooker.get_external_ip()
        if not args.lookup:
            return
    else:
        ip_address = args.ip_address or input("Please enter the IP address to look up: ")

    if not ip_address:
        print_color("No IP address provided.", "red")
        return

    # Dynamically register environment variables for all sources
    for source in IPLooker.LOOKUP_SOURCES:
        var_name = source.get_env_var_name()
        env.add_var(var_name, required=False, secret=True)

    IPLooker(ip_address)


if __name__ == "__main__":
    main()
