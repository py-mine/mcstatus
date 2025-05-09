from __future__ import annotations

from typing import cast

import dns.asyncresolver
import dns.resolver
from dns.rdatatype import RdataType
from dns.rdtypes.IN.A import A as ARecordAnswer
from dns.rdtypes.IN.SRV import SRV as SRVRecordAnswer  # noqa: N811 # constant imported as non constant (it's class)


def resolve_a_record(hostname: str, lifetime: float | None = None) -> str:
    """Perform a DNS resolution for an A record to given hostname

    :param hostname: The address to resolve for.
    :return: The resolved IP address from the A record
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by :func:`dns.resolver.resolve`.
        Most notably this will be :exc:`dns.exception.Timeout`, :exc:`dns.resolver.NXDOMAIN`
        and :exc:`dns.resolver.NoAnswer`
    """
    answers = dns.resolver.resolve(hostname, RdataType.A, lifetime=lifetime, search=True)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = cast(ARecordAnswer, answers[0])
    ip = str(answer).rstrip(".")
    return ip


async def async_resolve_a_record(hostname: str, lifetime: float | None = None) -> str:
    """Asynchronous alternative to :func:`.resolve_a_record`.

    For more details, check it.
    """
    answers = await dns.asyncresolver.resolve(hostname, RdataType.A, lifetime=lifetime, search=True)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = cast(ARecordAnswer, answers[0])
    ip = str(answer).rstrip(".")
    return ip


def resolve_srv_record(query_name: str, lifetime: float | None = None) -> tuple[str, int]:
    """Perform a DNS resolution for SRV record pointing to the Java Server.

    :param query_name: The address to resolve for.
    :return: A tuple of host string and port number
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by :func:`dns.resolver.resolve`.
        Most notably this will be :exc:`dns.exception.Timeout`, :exc:`dns.resolver.NXDOMAIN`
        and :exc:`dns.resolver.NoAnswer`
    """
    answers = dns.resolver.resolve(query_name, RdataType.SRV, lifetime=lifetime, search=True)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = cast(SRVRecordAnswer, answers[0])
    host = str(answer.target).rstrip(".")
    port = int(answer.port)
    return host, port


async def async_resolve_srv_record(query_name: str, lifetime: float | None = None) -> tuple[str, int]:
    """Asynchronous alternative to :func:`.resolve_srv_record`.

    For more details, check it.
    """
    answers = await dns.asyncresolver.resolve(query_name, RdataType.SRV, lifetime=lifetime, search=True)
    # There should only be one answer here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    answer = cast(SRVRecordAnswer, answers[0])
    host = str(answer.target).rstrip(".")
    port = int(answer.port)
    return host, port


def resolve_mc_srv(hostname: str, lifetime: float | None = None) -> tuple[str, int]:
    """Resolve SRV record for a minecraft server on given hostname.

    :param str hostname: The address, without port, on which an SRV record is present.
    :return: Obtained target and port from the SRV record, on which the server should live on.
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by :func:`dns.resolver.resolve`.
        Most notably this will be :exc:`dns.exception.Timeout`, :exc:`dns.resolver.NXDOMAIN`
        and :exc:`dns.resolver.NoAnswer`.
    """
    return resolve_srv_record("_minecraft._tcp." + hostname, lifetime=lifetime)


async def async_resolve_mc_srv(hostname: str, lifetime: float | None = None) -> tuple[str, int]:
    """Asynchronous alternative to :func:`.resolve_mc_srv`.

    For more details, check it.
    """
    return await async_resolve_srv_record("_minecraft._tcp." + hostname, lifetime=lifetime)
