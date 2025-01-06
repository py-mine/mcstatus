from __future__ import annotations

import ipaddress
import sys
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import dns.resolver
import pytest
from dns.rdatatype import RdataType

from mcstatus.address import Address, async_minecraft_srv_address_lookup, minecraft_srv_address_lookup


class TestSRVLookup:
    @pytest.mark.parametrize("exception", [dns.resolver.NXDOMAIN, dns.resolver.NoAnswer])
    def test_address_no_srv(self, exception):
        with patch("dns.resolver.resolve") as resolve:
            resolve.side_effect = [exception]
            address = minecraft_srv_address_lookup("example.org", default_port=25565, lifetime=3)
            resolve.assert_called_once_with("_minecraft._tcp.example.org", RdataType.SRV, lifetime=3, search=True)

        assert address.host == "example.org"
        assert address.port == 25565

    def test_address_with_srv(self):
        with patch("dns.resolver.resolve") as resolve:
            answer = Mock()
            answer.target = "different.example.org."
            answer.port = 12345
            resolve.return_value = [answer]

            address = minecraft_srv_address_lookup("example.org", lifetime=3)
            resolve.assert_called_once_with("_minecraft._tcp.example.org", RdataType.SRV, lifetime=3, search=True)
        assert address.host == "different.example.org"
        assert address.port == 12345

    @pytest.mark.asyncio
    @pytest.mark.parametrize("exception", [dns.resolver.NXDOMAIN, dns.resolver.NoAnswer])
    async def test_async_address_no_srv(self, exception):
        with patch("dns.asyncresolver.resolve") as resolve:
            resolve.side_effect = [exception]
            address = await async_minecraft_srv_address_lookup("example.org", default_port=25565, lifetime=3)
            resolve.assert_called_once_with("_minecraft._tcp.example.org", RdataType.SRV, lifetime=3, search=True)

        assert address.host == "example.org"
        assert address.port == 25565

    @pytest.mark.asyncio
    async def test_async_address_with_srv(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            answer = Mock()
            answer.target = "different.example.org."
            answer.port = 12345
            resolve.return_value = [answer]

            address = await async_minecraft_srv_address_lookup("example.org", lifetime=3)
            resolve.assert_called_once_with("_minecraft._tcp.example.org", RdataType.SRV, lifetime=3, search=True)
        assert address.host == "different.example.org"
        assert address.port == 12345


class TestAddressValidity:
    @pytest.mark.parametrize(
        "address,port",
        [
            ("example.org", 25565),
            ("192.168.0.100", 54321),
            ("2345:0425:2CA1:0000:0000:0567:5673:23b5", 100),
            ("2345:0425:2CA1::0567:5673:23b5", 12345),
        ],
    )
    def test_address_validation_valid(self, address, port):
        Address._ensure_validity(address, port)

    @pytest.mark.parametrize(
        "address,port,exception",
        [
            # Out of range port
            ("example.org", 100_000, ValueError),
            ("example.org", -1, ValueError),
            # Invalid types
            ("example.org", "25565", TypeError),
            (25565, "example.org", TypeError),
            (("example.org", 25565), None, TypeError),
            (0, 0, TypeError),
            ("", "", TypeError),
        ],
    )
    def test_address_validation_invalid(self, address, port, exception):
        with pytest.raises(exception):
            Address._ensure_validity(address, port)


class TestAddressConstructing:
    def test_init_constructor(self):
        addr = Address("example.org", 25565)
        assert addr.host == "example.org"
        assert addr.port == 25565

    def test_tuple_behavior(self):
        addr = Address("example.org", 25565)
        assert isinstance(addr, tuple)
        assert len(addr) == 2
        assert addr[0] == "example.org"
        assert addr[1] == 25565

    def test_from_tuple_constructor(self):
        addr = Address.from_tuple(("example.org", 12345))
        assert addr.host == "example.org"
        assert addr.port == 12345

    def test_from_path_constructor(self):
        addr = Address.from_path(Path("example.org:25565"))
        assert addr.host == "example.org"
        assert addr.port == 25565

    def test_address_with_port_no_default(self):
        addr = Address.parse_address("example.org:25565")
        assert addr.host == "example.org"
        assert addr.port == 25565

    def test_address_with_port_default(self):
        addr = Address.parse_address("example.org:25565", default_port=12345)
        assert addr.host == "example.org"
        assert addr.port == 25565

    def test_address_without_port_default(self):
        addr = Address.parse_address("example.org", default_port=12345)
        assert addr.host == "example.org"
        assert addr.port == 12345

    def test_address_without_port(self):
        with pytest.raises(ValueError):
            Address.parse_address("example.org")

    def test_address_with_invalid_port(self):
        with pytest.raises(ValueError):
            Address.parse_address("example.org:port")

    def test_address_with_multiple_ports(self):
        with pytest.raises(ValueError):
            Address.parse_address("example.org:12345:25565")


class TestAddressIPResolving:
    def setup_method(self):
        self.host_addr = Address("example.org", 25565)
        self.ipv4_addr = Address("1.1.1.1", 25565)
        self.ipv6_addr = Address("::1", 25565)

    def test_ip_resolver_with_hostname(self):
        with patch("dns.resolver.resolve") as resolve:
            answer = MagicMock()
            cast(MagicMock, answer.__str__).return_value = "48.225.1.104."
            resolve.return_value = [answer]

            resolved_ip = self.host_addr.resolve_ip(lifetime=3)

            resolve.assert_called_once_with(self.host_addr.host, RdataType.A, lifetime=3, search=True)
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == "48.225.1.104"

    @pytest.mark.asyncio
    async def test_async_ip_resolver_with_hostname(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            answer = MagicMock()
            cast(MagicMock, answer.__str__).return_value = "48.225.1.104."
            resolve.return_value = [answer]

            resolved_ip = await self.host_addr.async_resolve_ip(lifetime=3)

            resolve.assert_called_once_with(self.host_addr.host, RdataType.A, lifetime=3, search=True)
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == "48.225.1.104"

    def test_ip_resolver_with_ipv4(self):
        with patch("dns.resolver.resolve") as resolve:
            resolved_ip = self.ipv4_addr.resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == self.ipv4_addr.host

    @pytest.mark.asyncio
    async def test_async_ip_resolver_with_ipv4(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            resolved_ip = await self.ipv4_addr.async_resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv4Address)
            assert str(resolved_ip) == self.ipv4_addr.host

    def test_ip_resolver_with_ipv6(self):
        with patch("dns.resolver.resolve") as resolve:
            resolved_ip = self.ipv6_addr.resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv6Address)
            assert str(resolved_ip) == self.ipv6_addr.host

    @pytest.mark.asyncio
    async def test_async_ip_resolver_with_ipv6(self):
        with patch("dns.asyncresolver.resolve") as resolve:
            resolved_ip = await self.ipv6_addr.async_resolve_ip(lifetime=3)

            resolve.assert_not_called()  # Make sure we didn't needlessly try to resolve
            assert isinstance(resolved_ip, ipaddress.IPv6Address)
            assert str(resolved_ip) == self.ipv6_addr.host

    def test_resolve_localhost(self):
        addr = Address("localhost", 25565)

        context_manager = pytest.warns(RuntimeWarning) if sys.platform == "darwin" else MagicMock()
        with context_manager:
            assert addr.resolve_ip() == ipaddress.ip_address("127.0.0.1")

    @pytest.mark.asyncio
    async def test_async_resolve_localhost(self):
        addr = Address("localhost", 25565)

        context_manager = pytest.warns(RuntimeWarning) if sys.platform == "darwin" else MagicMock()
        with context_manager:
            assert await addr.async_resolve_ip() == ipaddress.ip_address("127.0.0.1")
