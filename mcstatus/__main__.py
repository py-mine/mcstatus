from __future__ import annotations

import dns.resolver
import sys
import json
import argparse
import socket
import dataclasses
from typing import TYPE_CHECKING

from mcstatus import JavaServer, BedrockServer
from mcstatus.responses import JavaStatusResponse
from mcstatus.motd import Motd

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    SupportedServers: TypeAlias = "JavaServer | BedrockServer"

PING_PACKET_FAIL_WARNING = (
    "warning: contacting {address} failed with a 'ping' packet but succeeded with a 'status' packet,\n"
    "         this is likely a bug in the server-side implementation.\n"
    '         (note: ping packet failed due to "{ping_exc}")\n'
    "         for more details, see: https://mcstatus.readthedocs.io/en/stable/pages/faq/\n"
)

QUERY_FAIL_WARNING = (
    "The server did not respond to the query protocol."
    "\nPlease ensure that the server has enable-query turned on,"
    " and that the necessary port (same as server-port unless query-port is set) is open in any firewall(s)."
    "\nSee https://wiki.vg/Query for further information."
)


def _motd(motd: Motd) -> str:
    """Formats MOTD for human-readable output, with leading line break
    if multiline."""
    s = motd.to_ansi()
    return f"\n{s}" if "\n" in s else f" {s}"


def _kind(serv: SupportedServers) -> str:
    if isinstance(serv, JavaServer):
        return "Java"
    elif isinstance(serv, BedrockServer):
        return "Bedrock"
    else:
        raise ValueError(f"unsupported server for kind: {serv}")


def _ping_with_fallback(server: SupportedServers) -> float:
    # bedrock doesn't have ping method
    if isinstance(server, BedrockServer):
        return server.status().latency

    # try faster ping packet first, falling back to status with a warning.
    ping_exc = None
    try:
        return server.ping(tries=1)
    except Exception as e:
        ping_exc = e

    latency = server.status().latency

    address = f"{server.address.host}:{server.address.port}"
    print(
        PING_PACKET_FAIL_WARNING.format(address=address, ping_exc=ping_exc),
        file=sys.stderr,
    )

    return latency


def ping_cmd(server: SupportedServers) -> int:
    print(_ping_with_fallback(server))
    return 0


def status_cmd(server: SupportedServers) -> int:
    response = server.status()

    java_res = response if isinstance(response, JavaStatusResponse) else None

    if not java_res:
        player_sample = ""
    elif java_res.players.sample is not None:
        player_sample = str([f"{player.name} ({player.id})" for player in java_res.players.sample])
    else:
        player_sample = "No players online"

    if player_sample:
        player_sample = " " + player_sample

    print(f"version: {_kind(server)} {response.version.name} (protocol {response.version.protocol})")
    print(f"motd:{_motd(response.motd)}")
    print(f"players: {response.players.online}/{response.players.max}{player_sample}")
    print(f"ping: {response.latency:.2f} ms")
    return 0


def json_cmd(server: SupportedServers) -> int:
    data = {"online": False, "kind": _kind(server)}

    status_res = query_res = exn = None
    try:
        status_res = server.status(tries=1)
    except Exception as e:
        exn = exn or e

    try:
        if isinstance(server, JavaServer):
            query_res = server.query(tries=1)
    except Exception as e:
        exn = exn or e

    # construct 'data' dict outside try/except to ensure data processing errors
    # are noticed.
    data["online"] = bool(status_res or query_res)
    if not data["online"]:
        assert exn, "server offline but no exception?"
        data["error"] = str(exn)

    if status_res is not None:
        data["status"] = dataclasses.asdict(status_res)

        # ensure we are overwriting the motd and not making a new dict field
        assert "motd" in data["status"], "motd field missing. has it been renamed?"
        data["status"]["motd"] = status_res.motd.simplify().to_minecraft()

    if query_res is not None:
        # TODO: QueryResponse is not (yet?) a dataclass
        data["query"] = qdata = {}

        qdata["ip"] = query_res.raw["hostip"]
        qdata["port"] = query_res.raw["hostport"]
        qdata["map"] = query_res.map_name
        qdata["plugins"] = query_res.software.plugins
        qdata["raw"] = query_res.raw

    json.dump(data, sys.stdout)
    return 0


def query_cmd(server: SupportedServers) -> int:
    if not isinstance(server, JavaServer):
        print("The 'query' protocol is only supported by Java servers.", file=sys.stderr)
        return 1

    try:
        response = server.query()
    except socket.timeout:
        print(QUERY_FAIL_WARNING, file=sys.stderr)
        return 1

    print(f"host: {response.raw['hostip']}:{response.raw['hostport']}")
    print(f"software: {_kind(server)} {response.software.version} {response.software.brand}")
    print(f"motd:{_motd(response.motd)}")
    print(f"plugins: {response.software.plugins}")
    print(f"players: {response.players.online}/{response.players.max} {response.players.list}")
    return 0


def main(argv: list[str] = sys.argv[1:]) -> int:
    parser = argparse.ArgumentParser(
        "mcstatus",
        description="""
        mcstatus provides an easy way to query 1.7 or newer Minecraft servers for any
        information they can expose. It provides three modes of access: query, status,
        ping and json.
        """,
    )

    parser.add_argument("address", help="The address of the server.")
    parser.add_argument("--bedrock", help="Specifies that 'address' is a Bedrock server (default: Java).", action="store_true")

    subparsers = parser.add_subparsers(title="commands", description="Command to run, defaults to 'status'.")
    parser.set_defaults(func=status_cmd)

    subparsers.add_parser("ping", help="Ping server for latency.").set_defaults(func=ping_cmd)
    subparsers.add_parser("status", help="Prints server status.").set_defaults(func=status_cmd)
    subparsers.add_parser(
        "query", help="Prints detailed server information. Must be enabled in servers' server.properties file."
    ).set_defaults(func=query_cmd)
    subparsers.add_parser(
        "json",
        help="Prints server status and query in json.",
    ).set_defaults(func=json_cmd)

    args = parser.parse_args(argv)
    lookup = JavaServer.lookup if not args.bedrock else BedrockServer.lookup

    try:
        server = lookup(args.address)
        return args.func(server)
    except (socket.timeout, socket.gaierror, dns.resolver.NoNameservers, ConnectionError, TimeoutError) as e:
        # catch and hide traceback for expected user-facing errors
        print(f"Error: {e!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
