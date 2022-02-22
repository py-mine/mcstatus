import ipaddress
import dns.resolver
import dns.asyncresolver
from typing import NamedTuple


class Address(NamedTuple):
    host: str
    port: int

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
            print(f"Resolved A record for {self.host} -> {ip_addr}")
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
            print(f"Resolved A record for {self.host} -> {ip_addr}")
            return ipaddress.ip_address(ip_addr)
