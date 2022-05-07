from __future__ import annotations

import socket
from dataclasses import asdict
from json import dumps as json_dumps

import click

from mcstatus import MCServer

server: MCServer = None  # type: ignore[assignment]  # This will be set with cli function


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("address")
def cli(address):
    """
    mcstatus provides an easy way to query Minecraft servers for
    any information they can expose. It provides three modes of
    access: query, status, and ping.

    Examples:

    \b
    $ mcstatus example.org ping
    21.120ms

    \b
    $ mcstatus example.org:1234 ping
    159.903ms

    \b
    $ mcstatus example.org status
    version: v1.8.8 (protocol 47)
    description: "A Minecraft Server"
    players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']

    \b
    $ mcstatus example.org query
    host: 93.148.216.34:25565
    software: v1.8.8 vanilla
    plugins: []
    motd: "A Minecraft Server"
    players: 1/20 ['Dinnerbone (61699b2e-d327-4a01-9f1e-0ea8c3f06bc6)']
    """
    global server
    server = MCServer.lookup(address)


@cli.command(short_help="basic server information")
def status():
    """
    Prints server status. Supported by all Minecraft
    servers that are version 1.7 or higher.
    """
    response = server.status()
    if response.players.list is not None:
        player_sample = str([f"{player.name} ({player.uuid})" for player in response.players.list])
    else:
        player_sample = "No players online"

    click.echo(f"version: v{response.version.name} (protocol {response.version.protocol})")
    click.echo(f'motd: "{response.motd}"')
    click.echo(f"players: {response.players.online}/{response.players.max} {player_sample}")


@cli.command(short_help="all available server information in json")
def json():
    """
    Prints server status and query in json. Supported by all Minecraft
    servers that are version 1.7 or higher.
    """
    try:
        status_res = server.status(tries=1)
        data = asdict(status_res)
        data["online"] = True
    except Exception:  # TODO: Check what this actually excepts
        data = {"online": False}
    click.echo(json_dumps(data))


@cli.command(short_help="detailed server information")
def query():
    """
    Prints detailed server information. Must be enabled in
    servers' server.properties file.
    """
    try:
        response = server.query()
    except socket.timeout:
        print(
            "The server did not respond to the query protocol."
            "\nPlease ensure that the server has enable-query turned on,"
            " and that the necessary port (same as server-port unless query-port is set) is open in any firewall(s)."
            "\nSee https://wiki.vg/Query for further information."
        )
        raise click.Abort()
    click.echo(f"host: {response.raw['hostip']}:{response.raw['hostport']}")
    click.echo(f"software: v{response.software.version} {response.software.brand}")
    click.echo(f"plugins: {response.software.plugins}")
    click.echo(f'motd: "{response.motd}"')
    click.echo(f"players: {response.players.online}/{response.players.max} {response.players.names}")


if __name__ == "__main__":
    cli()  # type: ignore[call-arg]
