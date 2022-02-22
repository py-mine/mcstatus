from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import NamedTuple, TYPE_CHECKING
from urllib.parse import urlparse

import dns.asyncresolver
import dns.resolver

if TYPE_CHECKING:
    from typing_extensions import Self


class Address(NamedTuple):
    host: str
    port: int

    @classmethod
    def from_tuple(cls, tup: tuple[str, int], /) -> Self:
        """Construct the class from a regular tuple of (host, port), commonly used for addresses."""
        return cls(host=tup[0], port=tup[1])

    @classmethod
    def from_path(cls, path: Path, /, *, default_port: int = None) -> Self:
        """Construct the class from a Path object.

        If path has a port specified, use it, if not fall back to default_port.
        In case default_port isn't available and port wasn't specified, raise ValueError.
        """
        address = str(path)
        return cls.parse_address(address, default_port=default_port)

    @classmethod
    def parse_address(cls, address: str, /, *, default_port: int = None) -> Self:
        """Parses a string address like 127.0.0.1:25565 into host and port parts

        If the address has a port specified, use it, if not, fall back to default_port.
        In case default_port isn't available and port wasn't specified, raise ValueError.
        """
        tmp = urlparse("//" + address)
        if not tmp.hostname:
            raise ValueError(f"Invalid address '{address}', can't parse.")

        if tmp.port is None:
            if default_port is not None:
                port = default_port
            else:
                raise ValueError(
                    f"Given address '{address}' doesn't contain port and default_port wasn't specified, can't parse."
                )
        else:
            port = tmp.port
        return cls(host=tmp.hostname, port=port)

    def resolve_ip(self, lifetime: float = None) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """Resolves a hostname's A record into an IP address.

        If the host is already an IP, this resolving is skipped
        and host is returned directly.

        :param lifetime:
            How many seconds a query should run before timing out.
            Default value for this is inherited from dns.resolver.resolve
        :raises dns.exception.DNSException:
            One of the exceptions possibly raised by dns.resolver.resolve
            Most notably this will be `dns.exception.Timeout` and `dns.resolver.NXDOMAIN`
        """
        try:
            return ipaddress.ip_address(self.host)
        except ValueError:
            # ValueError is raised if the given address wasn't valid
            # this means it's a hostname and we should try to resolve
            # the A record
            answers = dns.resolver.resolve(self.host, "A", lifetime=lifetime)
            # There should only be one answer here, though in case the server
            # does actually point to multiple IPs, we just pick the first one
            answer = answers[0]
            ip_addr = str(answer).rstrip(".")
            return ipaddress.ip_address(ip_addr)

    async def async_resolve_ip(self, lifetime: float = None) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """Resolves a hostname's A record into an IP address.

        See the docstring for `resolve_ip` for further info. This function is purely
        an async alternative to it.
        """
        try:
            return ipaddress.ip_address(self.host)
        except ValueError:
            # ValueError is raised if the given address wasn't valid
            # this means it's a hostname and we should try to resolve
            # the A record
            answers = await dns.asyncresolver.resolve(self.host, "A", lifetime=lifetime)
            # There should only be one answer here, though in case the server
            # does actually point to multiple IPs, we just pick the first one
            answer = answers[0]
            ip_addr = str(answer).rstrip(".")
            return ipaddress.ip_address(ip_addr)
