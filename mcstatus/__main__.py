from __future__ import annotations

import sys
import argparse
import socket
from typing import TYPE_CHECKING
from json import dumps as json_dumps

from mcstatus import JavaServer, BedrockServer
from mcstatus.responses import JavaStatusResponse

if TYPE_CHECKING:
    SupportedServers = JavaServer | BedrockServer


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
    motd = response.motd.to_ansi()
    motd = f"\n{motd}" if "\n" in motd else f" {motd}"
    print(f"motd:{motd}")
    print(f"players: {response.players.online}/{response.players.max}{player_sample}")
    print(f"ping: {response.latency:.2f} ms")
    return 0


def json(server: SupportedServers) -> int:
    data = {}
    data["online"] = False
    data["kind"] = server.kind()
    # Build data with responses and quit on exception
    try:
        status_res = server.status(tries=1)
        java_res = status_res if isinstance(status_res, JavaStatusResponse) else None
        data["version"] = status_res.version.name
        data["protocol"] = status_res.version.protocol
        data["motd"] = status_res.motd.to_minecraft()
        data["player_count"] = status_res.players.online
        data["player_max"] = status_res.players.max
        data["players"] = []
        if java_res and java_res.players.sample is not None:
            data["players"] = [{"name": player.name, "id": player.id} for player in java_res.players.sample]

        data["ping"] = status_res.latency
        data["online"] = True

        if isinstance(server, JavaServer):
            query_res = server.query(tries=1)
            data["host_ip"] = query_res.raw["hostip"]
            data["host_port"] = query_res.raw["hostport"]
            data["map"] = query_res.map
            data["plugins"] = query_res.software.plugins
    except Exception:  # TODO: Check what this actually excepts
        pass

    print(json_dumps(data))
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
    print(f"plugins: {response.software.plugins}")
    motd = response.motd.to_ansi()
    motd = f"\n{motd}" if "\n" in motd else f" {motd}"
    print(f"motd:{motd}")
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
