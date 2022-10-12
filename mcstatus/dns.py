from __future__ import annotations

import dns.asyncresolver
import dns.resolver
from dns.rdatatype import RdataType


def resolve_a_record(hostname: str, lifetime: float | None = None) -> str:
    """Perform a DNS resolution for an A record to given hostname

    :param str hostname: The address to resolve for.
    :return: The resolved IP address from the A record
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by dns.resolver.resolve
        Most notably this will be `dns.exception.Timeout`, `dns.resolver.NXDOMAIN` and `dns.resolver.NoAnswer`
    """
    answers = dns.resolver.resolve(hostname, RdataType.A, lifetime=lifetime)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = answers[0]
    ip = str(answer).rstrip(".")
    return ip


async def async_resolve_a_record(hostname: str, lifetime: float | None = None) -> str:
    """Asynchronous alternative to resolve_a_record.

    For more details, check the docstring of resolve_a_record function.
    """
    answers = await dns.asyncresolver.resolve(hostname, RdataType.A, lifetime=lifetime)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = answers[0]
    ip = str(answer).rstrip(".")
    return ip


def resolve_srv_record(query_name: str, lifetime: float | None = None) -> tuple[str, int]:
    """Perform a DNS resolution for SRV record pointing to the Java Server.

    :param str address: The address to resolve for.
    :return: A tuple of host string and port number
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by dns.resolver.resolve
        Most notably this will be `dns.exception.Timeout`, `dns.resolver.NXDOMAIN` and `dns.resolver.NoAnswer`
    """
    answers = dns.resolver.resolve(query_name, RdataType.SRV, lifetime=lifetime)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = answers[0]
    host = str(answer.target).rstrip(".")
    port = int(answer.port)
    return host, port


async def async_resolve_srv_record(query_name: str, lifetime: float | None = None) -> tuple[str, int]:
    """Asynchronous alternative to resolve_srv_record.

    For more details, check the docstring of resolve_srv_record function.
    """
    answers = await dns.asyncresolver.resolve(query_name, RdataType.SRV, lifetime=lifetime)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = answers[0]
    host = str(answer.target).rstrip(".")
    port = int(answer.port)
    return host, port


def resolve_mc_srv(hostname: str, lifetime: float | None = None) -> tuple[str, int]:
    """Resolve SRV record for a minecraft server on given hostname.

    :param str address: The address, without port, on which an SRV record is present.
    :return: Obtained target and port from the SRV record, on which the server should live on.
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by dns.resolver.resolve
        Most notably this will be `dns.exception.Timeout`, `dns.resolver.NXDOMAIN` and `dns.resolver.NoAnswer`

    Returns obtained target and port from the SRV record, on which
    the minecraft server should live on.
    """
    return resolve_srv_record("_minecraft._tcp." + hostname, lifetime=lifetime)


async def async_resolve_mc_srv(hostname: str, lifetime: float | None = None) -> tuple[str, int]:
    """Asynchronous alternative to resolve_mc_srv.

    For more details, check the docstring of resolve_mc_srv function.
    """
    return await async_resolve_srv_record("_minecraft._tcp." + hostname, lifetime=lifetime)
