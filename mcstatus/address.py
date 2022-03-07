from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import NamedTuple, Optional, TYPE_CHECKING, Tuple, Union
from urllib.parse import urlparse

import dns.asyncresolver
import dns.resolver
from dns.rdatatype import RdataType

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ("Address", "minecraft_srv_address_lookup", "async_minecraft_srv_address_lookup")


def _valid_urlparse(address: str) -> Tuple[str, Optional[int]]:
    """Parses a string address like 127.0.0.1:25565 into host and port parts

    If the address doesn't have a specified port, None will be returned instead.

    :raises ValueError:
        Unable to resolve hostname of given address
    """
    tmp = urlparse("//" + address)
    if not tmp.hostname:
        raise ValueError(f"Invalid address '{address}', can't parse.")

    return tmp.hostname, tmp.port


class _AddressBase(NamedTuple):
    host: str
    port: int


class Address(_AddressBase):
    def __new__(cls, *a, **kw):
        instance = super().__new__(cls, *a, **kw)

        # Ensure the validity of the address before allowing it's creation
        cls._ensure_validity(instance.host, instance.port)

        return instance

    @staticmethod
    def _ensure_validity(host: object, port: object) -> None:
        if not isinstance(host, str):
            raise TypeError(f"Host must be a string address, got {type(host)} ({host!r})")
        if not isinstance(port, int):
            raise TypeError(f"Port must be an integer port number, got {type(port)} ({port!r})")
        if port > 65535 or port < 0:
            raise ValueError(f"Port must be within the allowed range (0-2^16), got {port!r}")

    @classmethod
    def from_tuple(cls, tup: Tuple[str, int]) -> Self:
        """Construct the class from a regular tuple of (host, port), commonly used for addresses."""
        return cls(host=tup[0], port=tup[1])

    @classmethod
    def from_path(cls, path: Path, *, default_port: Optional[int] = None) -> Self:
        """Construct the class from a Path object.

        If path has a port specified, use it, if not fall back to default_port.
        In case default_port isn't available and port wasn't specified, raise ValueError.
        """
        address = str(path)
        return cls.parse_address(address, default_port=default_port)

    @classmethod
    def parse_address(cls, address: str, *, default_port: Optional[int] = None) -> Self:
        """Parses a string address like 127.0.0.1:25565 into host and port parts

        If the address has a port specified, use it, if not, fall back to default_port.

        :raises ValueError:
            Either the address isn't valid and can't be parsed,
            or it lacks a port and `default_port` wasn't specified.
        """
        hostname, port = _valid_urlparse(address)
        if port is None:
            if default_port is not None:
                port = default_port
            else:
                raise ValueError(
                    f"Given address '{address}' doesn't contain port and default_port wasn't specified, can't parse."
                )
        return cls(host=hostname, port=port)

    def resolve_ip(self, lifetime: Optional[float] = None) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
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
            answers = dns.resolver.resolve(self.host, RdataType.A, lifetime=lifetime)
            # There should only be one answer here, though in case the server
            # does actually point to multiple IPs, we just pick the first one
            answer = answers[0]
            ip_addr = str(answer).rstrip(".")
            return ipaddress.ip_address(ip_addr)

    async def async_resolve_ip(self, lifetime: Optional[float] = None) -> Union[ipaddress.IPv4Address, ipaddress.IPv6Address]:
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
            answers = await dns.asyncresolver.resolve(self.host, RdataType.A, lifetime=lifetime)
            # There should only be one answer here, though in case the server
            # does actually point to multiple IPs, we just pick the first one
            answer = answers[0]
            ip_addr = str(answer).rstrip(".")
            return ipaddress.ip_address(ip_addr)


def minecraft_srv_address_lookup(address: str, *, default_port: Optional[int] = None, lifetime: float = 3) -> Address:
    """Parses the address, if it doesn't include port, tries SRV record, if it's not there, falls back on default_port

    This function essentially mimics the address field of a minecraft java server. It expects an address like
    '192.168.0.100:25565', if this address does contain a port, it will simply use it. If it doesn't, it will try
    to perform an SRV lookup, which if found, will contain the info on which port to use. If there's no SRV record,
    this will fall back to the given default_port.

    :param address:
        The same address which would be used in minecraft's server address field.
        Can look like: '127.0.0.1', or '192.168.0.100:12345', or 'mc.hypixel.net', or 'example.com:12345'.
    :param lifetime:
        How many seconds a query should run before timing out.
        Default value for this is inherited from dns.resolver.resolve
    :raises ValueError:
        Either the address isn't valid and can't be parsed,
        or it lacks a port, SRV record isn't present, and `default_port` wasn't specified.
    """
    host, port = _valid_urlparse(address)

    # If we didn't find the port, check for an SRV record, pointing us
    # to the port which we should use. If there's no such record, fall
    # back to the default port.
    if port is None:
        try:
            answers = dns.resolver.resolve("_minecraft._tcp." + host, RdataType.SRV, lifetime=lifetime)
        except dns.resolver.NXDOMAIN:
            if default_port is None:
                raise ValueError(
                    f"Given address '{address}' doesn't contain port, doesn't have an SRV record pointing to a port,"
                    " and default_port wasn't specified, can't parse."
                )
            else:
                return Address(host, default_port)
        else:
            # The record was found, use it instead
            answer = answers[0]
            host = str(answer.target).rstrip(".")
            port = int(answer.port)

    return Address(host, port)


async def async_minecraft_srv_address_lookup(
    address: str,
    *,
    default_port: Optional[int] = None,
    lifetime: float = 3,
) -> Address:
    """Parses the address, if it doesn't include port, tries SRV record, if it's not there, falls back on default_port

    This function is an async alternative to minecraft_srv_address_lookup, check it's docstring for more details.
    """
    host, port = _valid_urlparse(address)

    # If we didn't find the port, check for an SRV record, pointing us
    # to the port which we should use. If there's no such record, fall
    # back to the default port.
    if port is None:
        try:
            answers = await dns.asyncresolver.resolve("_minecraft._tcp." + host, RdataType.SRV, lifetime=lifetime)
        except dns.resolver.NXDOMAIN:
            if default_port is None:
                raise ValueError(
                    f"Given address '{address}' doesn't contain port, doesn't have an SRV record pointing to a port,"
                    " and default_port wasn't specified, can't parse."
                )
            else:
                return Address(host, default_port)
        else:
            # The record was found, use it instead
            answer = answers[0]
            host = str(answer.target).rstrip(".")
            port = int(answer.port)

    return Address(host, port)