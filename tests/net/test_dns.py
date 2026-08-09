from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import patch

import dns.exception
import dns.message
import dns.name
import dns.rdata
import dns.rdataclass
import dns.resolver
import pytest
from dns.rdatatype import RdataType

from mcstatus._net.dns import async_resolve_a_record, resolve_a_record

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


def dns_answer(record_type: RdataType, ip: str | None) -> dns.resolver.Answer:
    qname = dns.name.from_text("example.org.")
    response = cast("dns.message.QueryMessage", dns.message.make_response(dns.message.make_query(qname, record_type)))
    if ip is not None:
        answer = response.find_rrset(dns.message.ANSWER, qname, dns.rdataclass.IN, record_type, create=True)
        answer.add(dns.rdata.from_text(dns.rdataclass.IN, record_type, ip), ttl=60)

    return dns.resolver.Answer(qname, record_type, dns.rdataclass.IN, response)


def dns_mock(
    answers: Mapping[RdataType, dns.resolver.Answer],
) -> Callable[..., dns.resolver.Answer]:
    def resolve(
        qname: dns.name.Name | str,
        rdtype: RdataType | str = RdataType.A,
        rdclass: dns.rdataclass.RdataClass | str = dns.rdataclass.IN,
        tcp: bool = False,  # ruff: ignore[boolean-default-value-positional-argument]
        source: str | None = None,
        raise_on_no_answer: bool = True,  # ruff: ignore[boolean-default-value-positional-argument]
        source_port: int = 0,
        lifetime: float | None = None,
        search: bool | None = None,
        backend: object | None = None,
    ) -> dns.resolver.Answer:
        answer = answers[RdataType.make(rdtype)]
        if answer.rrset is None and raise_on_no_answer:
            raise dns.resolver.NoAnswer(response=answer.response)
        return answer

    return resolve


class TestARecordResolution:
    def test_prefers_ipv4_record(self):
        answers = {
            RdataType.A: dns_answer(RdataType.A, "192.0.2.1"),
            RdataType.AAAA: dns_answer(RdataType.AAAA, "2001:db8::1"),
        }
        with patch("dns.resolver.resolve", side_effect=dns_mock(answers)):
            assert resolve_a_record("example.org", lifetime=3) == "192.0.2.1"

    def test_falls_back_to_ipv6_record(self):
        with patch(
            "dns.resolver.resolve",
            side_effect=dns_mock(
                {
                    RdataType.A: dns_answer(RdataType.A, None),
                    RdataType.AAAA: dns_answer(RdataType.AAAA, "2001:db8::1"),
                }
            ),
        ):
            assert resolve_a_record("example.org", lifetime=3) == "2001:db8::1"

    @pytest.mark.parametrize("exception", [dns.exception.Timeout, dns.resolver.NXDOMAIN])
    def test_propagates_resolution_failure(self, exception: type[dns.exception.DNSException]):
        with (
            patch("dns.resolver.resolve", side_effect=exception),
            pytest.raises(exception),
        ):
            _ = resolve_a_record("example.org")

    async def test_async_prefers_ipv4_record(self):
        answers = {
            RdataType.A: dns_answer(RdataType.A, "192.0.2.1"),
            RdataType.AAAA: dns_answer(RdataType.AAAA, "2001:db8::1"),
        }

        with patch(
            "dns.asyncresolver.resolve",
            side_effect=dns_mock(answers),
        ):
            assert await async_resolve_a_record("example.org", lifetime=3) == "192.0.2.1"

    async def test_async_falls_back_to_ipv6_record(self):
        with patch(
            "dns.asyncresolver.resolve",
            side_effect=dns_mock(
                {
                    RdataType.A: dns_answer(RdataType.A, None),
                    RdataType.AAAA: dns_answer(RdataType.AAAA, "2001:db8::1"),
                }
            ),
        ):
            assert await async_resolve_a_record("example.org") == "2001:db8::1"

    @pytest.mark.parametrize("exception", [dns.exception.Timeout, dns.resolver.NXDOMAIN])
    async def test_async_propagates_resolution_failure(self, exception: type[dns.exception.DNSException]):
        with (
            patch("dns.asyncresolver.resolve", side_effect=exception),
            pytest.raises(exception),
        ):
            _ = await async_resolve_a_record("example.org")

    async def test_async_raises_no_answer_when_no_records_exist(self):
        with (
            patch(
                "dns.asyncresolver.resolve",
                side_effect=dns_mock(
                    {
                        RdataType.A: dns_answer(RdataType.A, None),
                        RdataType.AAAA: dns_answer(RdataType.AAAA, None),
                    }
                ),
            ),
            pytest.raises(dns.resolver.NoAnswer),
        ):
            _ = await async_resolve_a_record("example.org")
