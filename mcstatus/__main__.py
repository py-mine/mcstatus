from __future__ import annotations

import sys
import json as _json
import argparse
import socket
import dataclasses
from typing import TYPE_CHECKING

from mcstatus import JavaServer, BedrockServer
from mcstatus.responses import JavaStatusResponse
from mcstatus.motd import Motd

if TYPE_CHECKING:
    SupportedServers = JavaServer | BedrockServer


def _motd(motd: Motd) -> str:
    """Formats MOTD for human-readable output, with leading line break
    if multiline."""
    s = motd.to_ansi()
    return f"\n{s}" if "\n" in s else f" {s}"


def ping(server: SupportedServers) -> int:
    # this method supports both Java and Bedrock.
    # only Java supports the `ping` packet, and even then not always:
    # https://github.com/py-mine/mcstatus/issues/850
    print(f"{server.status().latency}")
    return 0


def status(server: SupportedServers) -> int:
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

    print(f"version: {server.kind()} {response.version.name} (protocol {response.version.protocol})")
    print(f"motd:{_motd(response.motd)}")
    print(f"players: {response.players.online}/{response.players.max}{player_sample}")
    print(f"ping: {response.latency:.2f} ms")
    return 0


def json(server: SupportedServers) -> int:
    data = {"online": False, "kind": server.kind()}

    status_res = query_res = None
    try:
        status_res = server.status(tries=1)
        if isinstance(server, JavaServer):
            query_res = server.query(tries=1)
    except Exception as e:
        if status_res is None:
            data["error"] = str(e)

    # construct 'data' dict outside try/except to ensure data processing errors
    # are noticed.
    data["online"] = bool(status_res or query_res)
    if status_res is not None:
        data["status"] = dataclasses.asdict(status_res)

        # XXX: hack to fixup MOTD serialisation. should be implemented elsewhere.
        assert "motd" in data["status"]
        data["status"]["motd"] = {"raw": status_res.motd.to_minecraft()}

    if query_res is not None:
        # TODO: QueryResponse is not (yet?) a dataclass
        data["query"] = qdata = {}

        qdata["host_ip"] = query_res.raw["hostip"]
        qdata["host_port"] = query_res.raw["hostport"]
        qdata["map"] = query_res.map
        qdata["plugins"] = query_res.software.plugins
        qdata["raw"] = query_res.raw

    _json.dump(data, sys.stdout)
    return 0


def query(server: SupportedServers) -> int:
    if not isinstance(server, JavaServer):
        print("The 'query' protocol is only supported by Java servers.", file=sys.stderr)
        return 1

    try:
        response = server.query()
    except socket.timeout:
        print(
            "The server did not respond to the query protocol."
            "\nPlease ensure that the server has enable-query turned on,"
            " and that the necessary port (same as server-port unless query-port is set) is open in any firewall(s)."
            "\nSee https://wiki.vg/Query for further information.",
            file=sys.stderr,
        )
        return 1

    print(f"host: {response.raw['hostip']}:{response.raw['hostport']}")
    print(f"software: v{response.software.version} {response.software.brand}")
    print(f"motd:{_motd(response.motd)}")
    print(f"plugins: {response.software.plugins}")
    print(f"players: {response.players.online}/{response.players.max} {response.players.names}")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        "mcstatus",
        description="""
        mcstatus provides an easy way to query Minecraft servers for
        any information they can expose. It provides three modes of
        access: query, status, ping and json.
        """,
    )

    parser.add_argument("address", help="The address of the server.")
    parser.add_argument("--bedrock", help="Specifies that 'address' is a Bedrock server (default: Java).", action="store_true")

    subparsers = parser.add_subparsers(title="commands", description="Command to run, defaults to 'status'.")
    parser.set_defaults(func=status)

    subparsers.add_parser("ping", help="Ping server for latency.").set_defaults(func=ping)
    subparsers.add_parser(
        "status", help="Prints server status. Supported by all Minecraft servers that are version 1.7 or higher."
    ).set_defaults(func=status)
    subparsers.add_parser(
        "query", help="Prints detailed server information. Must be enabled in servers' server.properties file."
    ).set_defaults(func=query)
    subparsers.add_parser(
        "json",
        help="Prints server status and query in json. Supported by all Minecraft servers that are version 1.7 or higher.",
    ).set_defaults(func=json)

    args = parser.parse_args(argv)
    lookup = JavaServer.lookup if not args.bedrock else BedrockServer.lookup
    server = lookup(args.address)

    try:
        return args.func(server)
    except (socket.timeout, socket.gaierror, ValueError) as e:
        # catch and hide traceback for expected user-facing errors
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
