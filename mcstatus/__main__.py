from __future__ import annotations

import argparse
import socket
from json import dumps as json_dumps

from mcstatus import JavaServer


def ping(server: JavaServer) -> None:
    print(f"{server.ping()}ms")


def status(server: JavaServer) -> None:
    response = server.status()
    if response.players.sample is not None:
        player_sample = str([f"{player.name} ({player.id})" for player in response.players.sample])
    else:
        player_sample = "No players online"

    print(f"version: v{response.version.name} (protocol {response.version.protocol})")
    print(f'motd: "{response.motd}"')
    print(f"players: {response.players.online}/{response.players.max} {player_sample}")


def json(server: JavaServer) -> None:
    data = {}
    data["online"] = False
    # Build data with responses and quit on exception
    try:
        status_res = server.status(tries=1)
        data["version"] = status_res.version.name
        data["protocol"] = status_res.version.protocol
        data["motd"] = status_res.motd
        data["player_count"] = status_res.players.online
        data["player_max"] = status_res.players.max
        data["players"] = []
        if status_res.players.sample is not None:
            data["players"] = [{"name": player.name, "id": player.id} for player in status_res.players.sample]

        data["ping"] = status_res.latency
        data["online"] = True

        query_res = server.query(tries=1)  # type: ignore[call-arg] # tries is supported with retry decorator
        data["host_ip"] = query_res.raw["hostip"]
        data["host_port"] = query_res.raw["hostport"]
        data["map"] = query_res.map
        data["plugins"] = query_res.software.plugins
    except Exception:  # TODO: Check what this actually excepts
        pass
    print(json_dumps(data))


def query(server: JavaServer) -> None:
    try:
        response = server.query()
    except socket.timeout:
        print(
            "The server did not respond to the query protocol."
            "\nPlease ensure that the server has enable-query turned on,"
            " and that the necessary port (same as server-port unless query-port is set) is open in any firewall(s)."
            "\nSee https://wiki.vg/Query for further information."
        )
        return
    print(f"host: {response.raw['hostip']}:{response.raw['hostport']}")
    print(f"software: v{response.software.version} {response.software.brand}")
    print(f"plugins: {response.software.plugins}")
    print(f'motd: "{response.motd}"')
    print(f"players: {response.players.online}/{response.players.max} {response.players.names}")


def main() -> None:
    parser = argparse.ArgumentParser(
        "mcstatus",
        description="""
        mcstatus provides an easy way to query Minecraft servers for
        any information they can expose. It provides three modes of
        access: query, status, ping and json.
        """,
    )

    parser.add_argument("address", help="The address of the server.")

    subparsers = parser.add_subparsers()
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

    args = parser.parse_args()
    server = JavaServer.lookup(args.address)

    args.func(server)


if __name__ == "__main__":
    main()
