# iplooker

This script will perform a lookup for an IP address using multiple sources. It can be used to get more information about an IP address, including the country, region, city, ISP, and any organization that may be associated to it.

## Usage

The script's primary purpose is looking up another IP address, but as a bonus feature, it can also tell you your current public IP address. You can even combine the two features to get a lookup for your public IP to see what other people might see if they were to look you up.

As of version 0.2.0, it can provide security information about an IP address as well, including whether an IP is a known VPN, proxy, Tor exit node, datacenter, or otherwise anonymous IP, if any of that information is provided by the lookup source.

As of version 0.4.0, it also supports IPv6 addresses.

Here are the commands you can use:

```bash
# Running with no arguments will prompt for an IP
iplooker

# You can specify an IP as part of the command
iplooker 12.34.56.78

# You can use `-m` or `--me` to check your public IP
iplooker -m
iplooker --me

# You can do both with `-l` or `--lookup`
iplooker -l
iplooker --lookup
```

## Installation

Install from `pip` with:

```bash
pip install iplooker
```

## Sources

It retrieves information from the following sources:

- ip-api.com
- ipapi.co
- ipapi.is
- ipdata.co
- ipgeolocation.io
- ipinfo.io
- iplocate.io

**NOTE:** The script currently uses my own API keys (obfuscated) for the lookups so that anyone can just download and go, but obviously this has potential for abuse. In the event that the script sees a lot of downloads or usage, I'll have to update it to default to free sources only with a bring-your-own-key approach, so please use responsibly!
