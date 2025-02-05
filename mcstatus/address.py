from __future__ import annotations

import ipaddress
import sys
import warnings
from pathlib import Path
from typing import NamedTuple, TYPE_CHECKING
from urllib.parse import urlparse

import dns.resolver

import mcstatus.dns

if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ("Address", "async_minecraft_srv_address_lookup", "minecraft_srv_address_lookup")


def _valid_urlparse(address: str) -> tuple[str, int | None]:
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
    """Intermediate NamedTuple class representing an address.

    We can't extend this class directly, since NamedTuples are slotted and
    read-only, however child classes can extend __new__, allowing us do some
    needed processing on child classes derived from this base class.
    """

    host: str
    port: int


class Address(_AddressBase):
    """Extension of a :class:`~typing.NamedTuple` of :attr:`.host` and :attr:`.port`, for storing addresses.

    This class inherits from :class:`tuple`, and is fully compatible with all functions
    which require pure ``(host, port)`` address tuples, but on top of that, it includes
    some neat functionalities, such as validity ensuring, alternative constructors
    for easy quick creation and methods handling IP resolving.

    .. note::
        The class is not a part of a Public API, but attributes :attr:`host` and :attr:`port` are a part of Public API.
    """

    def __init__(self, host: str, port: int):
        # We don't pass the host & port args to super's __init__, because NamedTuples handle
        # everything from __new__ and the passed self already has all of the parameters set.
        super().__init__()

        self._cached_ip: ipaddress.IPv4Address | ipaddress.IPv6Address | None = None

        # Make sure the address is valid
        self._ensure_validity(self.host, self.port)

    @staticmethod
    def _ensure_validity(host: object, port: object) -> None:
        if not isinstance(host, str):
            raise TypeError(f"Host must be a string address, got {type(host)} ({host!r})")
        if not isinstance(port, int):
            raise TypeError(f"Port must be an integer port number, got {type(port)} ({port!r})")
        if port > 65535 or port < 0:
            raise ValueError(f"Port must be within the allowed range (0-2^16), got {port!r}")

    @classmethod
    def from_tuple(cls, tup: tuple[str, int]) -> Self:
        """Construct the class from a regular tuple of ``(host, port)``, commonly used for addresses."""
        return cls(host=tup[0], port=tup[1])

    @classmethod
    def from_path(cls, path: Path, *, default_port: int | None = None) -> Self:
        """Construct the class from a :class:`~pathlib.Path` object.

        If path has a port specified, use it, if not fall back to ``default_port`` kwarg.
        In case ``default_port`` isn't provided and port wasn't specified, raise :exc:`ValueError`.
        """
        address = str(path)
        return cls.parse_address(address, default_port=default_port)

    @classmethod
    def parse_address(cls, address: str, *, default_port: int | None = None) -> Self:
        """Parses a string address like ``127.0.0.1:25565`` into :attr:`.host` and :attr:`.port` parts.

        If the address has a port specified, use it, if not, fall back to ``default_port`` kwarg.

        :raises ValueError:
            Either the address isn't valid and can't be parsed,
            or it lacks a port and ``default_port`` wasn't specified.
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

    def resolve_ip(self, lifetime: float | None = None) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """Resolves a hostname's A record into an IP address.

        If the host is already an IP, this resolving is skipped
        and host is returned directly.

        :param lifetime:
            How many seconds a query should run before timing out.
            Default value for this is inherited from :func:`dns.resolver.resolve`.
        :raises dns.exception.DNSException:
            One of the exceptions possibly raised by :func:`dns.resolver.resolve`.
            Most notably this will be :exc:`dns.exception.Timeout` and :exc:`dns.resolver.NXDOMAIN`
        """
        if self._cached_ip is not None:
            return self._cached_ip

        host = self.host
        if self.host == "localhost" and sys.platform == "darwin":
            host = "127.0.0.1"
            warnings.warn(
                "On macOS because of some mysterious reasons we can't resolve localhost into IP. "
                "Please, replace 'localhost' with '127.0.0.1' (or '::1' for IPv6) in your code to remove this warning.",
                category=RuntimeWarning,
                stacklevel=2,
            )

        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            # ValueError is raised if the given address wasn't valid
            # this means it's a hostname and we should try to resolve
            # the A record
            ip_addr = mcstatus.dns.resolve_a_record(self.host, lifetime=lifetime)
            ip = ipaddress.ip_address(ip_addr)

        self._cached_ip = ip
        return self._cached_ip

    async def async_resolve_ip(self, lifetime: float | None = None) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
        """Resolves a hostname's A record into an IP address.

        See the docstring for :meth:`.resolve_ip` for further info. This function is purely
        an async alternative to it.
        """
        if self._cached_ip is not None:
            return self._cached_ip

        host = self.host
        if self.host == "localhost" and sys.platform == "darwin":
            host = "127.0.0.1"
            warnings.warn(
                "On macOS because of some mysterious reasons we can't resolve localhost into IP. "
                "Please, replace 'localhost' with '127.0.0.1' (or '::1' for IPv6) in your code to remove this warning.",
                category=RuntimeWarning,
                stacklevel=2,
            )

        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            # ValueError is raised if the given address wasn't valid
            # this means it's a hostname and we should try to resolve
            # the A record
            ip_addr = await mcstatus.dns.async_resolve_a_record(self.host, lifetime=lifetime)
            ip = ipaddress.ip_address(ip_addr)

        self._cached_ip = ip
        return self._cached_ip


def minecraft_srv_address_lookup(
    address: str,
    *,
    default_port: int | None = None,
    lifetime: float | None = None,
) -> Address:
    """Lookup the SRV record for a Minecraft server.

    Firstly it parses the address, if it doesn't include port, tries SRV record, and if it's not there,
    falls back on ``default_port``.

    This function essentially mimics the address field of a Minecraft Java server. It expects an address like
    ``192.168.0.100:25565``, if this address does contain a port, it will simply use it. If it doesn't, it will try
    to perform an SRV lookup, which if found, will contain the info on which port to use. If there's no SRV record,
    this will fall back to the given ``default_port``.

    :param address:
        The same address which would be used in minecraft's server address field.
        Can look like: ``127.0.0.1``, or ``192.168.0.100:12345``, or ``mc.hypixel.net``, or ``example.com:12345``.
    :param lifetime:
        How many seconds a query should run before timing out.
        Default value for this is inherited from :func:`dns.resolver.resolve`.
    :raises ValueError:
        Either the address isn't valid and can't be parsed,
        or it lacks a port, SRV record isn't present, and ``default_port`` wasn't specified.
    """
    host, port = _valid_urlparse(address)

    # If we found a port in the address, there's nothing more we need
    if port is not None:
        return Address(host, port)

    # Otherwise, try to check for an SRV record, pointing us to the
    # port which we should use. If there's no such record, fall back
    # to the default_port (if it's defined).
    try:
        host, port = mcstatus.dns.resolve_mc_srv(host, lifetime=lifetime)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        if default_port is None:
            raise ValueError(
                f"Given address '{address}' doesn't contain port, doesn't have an SRV record pointing to a port,"
                " and default_port wasn't specified, can't parse."
            )
        port = default_port

    return Address(host, port)


async def async_minecraft_srv_address_lookup(
    address: str,
    *,
    default_port: int | None = None,
    lifetime: float | None = None,
) -> Address:
    """Just an async alternative to :func:`.minecraft_srv_address_lookup`, check it for more details."""
    host, port = _valid_urlparse(address)

    # If we found a port in the address, there's nothing more we need
    if port is not None:
        return Address(host, port)

    # Otherwise, try to check for an SRV record, pointing us to the
    # port which we should use. If there's no such record, fall back
    # to the default_port (if it's defined).
    try:
        host, port = await mcstatus.dns.async_resolve_mc_srv(host, lifetime=lifetime)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        if default_port is None:
            raise ValueError(
                f"Given address '{address}' doesn't contain port, doesn't have an SRV record pointing to a port,"
                " and default_port wasn't specified, can't parse."
            )
        port = default_port

    return Address(host, port)
