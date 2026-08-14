from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, cast

import dns.asyncresolver
import dns.resolver
from dns.rdatatype import RdataType

if TYPE_CHECKING:
    from dns.rdtypes.IN.A import A as ARecordAnswer
    from dns.rdtypes.IN.AAAA import AAAA as AAAARecordAnswer  # ruff: ignore[constant-imported-as-non-constant]
    from dns.rdtypes.IN.SRV import SRV as SRVRecordAnswer  # ruff: ignore[constant-imported-as-non-constant]

__all__ = [
    "async_resolve_a_record",
    "async_resolve_mc_srv",
    "async_resolve_srv_record",
    "resolve_a_record",
    "resolve_mc_srv",
    "resolve_srv_record",
]


def resolve_a_record(hostname: str, lifetime: float | None = None) -> str:
    """Perform a DNS resolution for an A/AAAA record to given hostname.

    :param hostname: The address to resolve for.
    :return: The resolved IP address from the A/AAAA record
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by :func:`dns.resolver.resolve`.
        Most notably this will be :exc:`dns.exception.Timeout`, :exc:`dns.resolver.NXDOMAIN`
        and :exc:`dns.resolver.NoAnswer` The `NoAnswer` exception will only be raised if
        neither A nor AAAA responses exist.
    """
    # Prioritize IPv4, if available
    try:
        answer = dns.resolver.resolve(hostname, RdataType.A, lifetime=lifetime, search=True)
    except dns.resolver.NoAnswer:
        answer = dns.resolver.resolve(hostname, RdataType.AAAA, lifetime=lifetime, search=True)

    # There should only be one record here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    record = cast("ARecordAnswer | AAAARecordAnswer", answer[0])
    ip = str(record).rstrip(".")
    return ip


async def async_resolve_a_record(hostname: str, lifetime: float | None = None) -> str:
    """Asynchronous alternative to :func:`.resolve_a_record`.

    For more details, check it.
    """
    a_task = asyncio.create_task(
        dns.asyncresolver.resolve(
            hostname,
            RdataType.A,
            lifetime=lifetime,
            search=True,
            raise_on_no_answer=False,
        )
    )
    aaaa_task = asyncio.create_task(
        dns.asyncresolver.resolve(
            hostname,
            RdataType.AAAA,
            lifetime=lifetime,
            search=True,
            raise_on_no_answer=False,
        )
    )

    # prioritize IPv4 if available
    try:
        a_answer = await a_task
    except BaseException:
        # Cancel the AAAA task if still running, then consume its result.
        # Any exception from the unused lookup is intentionally discarded.
        _ = aaaa_task.cancel()
        _ = await asyncio.gather(aaaa_task, return_exceptions=True)
        raise

    if a_answer.rrset is not None:
        answer = a_answer

        # Cancel the AAAA task if still running, then consume its result.
        # Any exception from the unused lookup is intentionally discarded.
        _ = aaaa_task.cancel()
        _ = await asyncio.gather(aaaa_task, return_exceptions=True)
    else:
        aaaa_answer = await aaaa_task
        if aaaa_answer.rrset is None:
            # TODO: Consider ExceptionGroup return once we support >=3.11
            raise dns.resolver.NoAnswer(response=aaaa_answer.response)

        answer = aaaa_answer

    for record in answer:
        record = cast("ARecordAnswer | AAAARecordAnswer", record)

        ip = str(record).rstrip(".")
        return ip

    raise RuntimeError(f"unreachable - DNS {answer=} was not a NoAnswer, but didn't have any records")


def resolve_srv_record(query_name: str, lifetime: float | None = None) -> tuple[str, int]:
    """Perform a DNS resolution for SRV record pointing to the Java Server.

    :param query_name: The address to resolve for.
    :return: A tuple of host string and port number
    :raises dns.exception.DNSException:
        One of the exceptions possibly raised by :func:`dns.resolver.resolve`.
        Most notably this will be :exc:`dns.exception.Timeout`, :exc:`dns.resolver.NXDOMAIN`
        and :exc:`dns.resolver.NoAnswer`
    """
    answer = dns.resolver.resolve(query_name, RdataType.SRV, lifetime=lifetime, search=True)
    # There should only be one record here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    record = cast("SRVRecordAnswer", answer[0])
    host = str(record.target).rstrip(".")
    port = int(record.port)
    return host, port


async def async_resolve_srv_record(query_name: str, lifetime: float | None = None) -> tuple[str, int]:
    """Asynchronous alternative to :func:`.resolve_srv_record`.

    For more details, check it.
    """
    answer = await dns.asyncresolver.resolve(query_name, RdataType.SRV, lifetime=lifetime, search=True)
    # There should only be one record here, though in case the server
    # does actually point to multiple IPs, we just pick the first one
    record = cast("SRVRecordAnswer", answer[0])
    host = str(record.target).rstrip(".")
    port = int(record.port)
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
