import io
import socket

from mcstatus import JavaServer, BedrockServer
from mcstatus.responses import JavaStatusResponse, BedrockStatusResponse, RawJavaResponse
from mcstatus.querier import QueryResponse

import os
import json
import contextlib
from unittest import mock
from unittest.mock import patch
import pytest

from mcstatus.__main__ import main as main_under_test, PING_PACKET_FAIL_WARNING, QUERY_FAIL_WARNING

JAVA_RAW_RESPONSE: RawJavaResponse = {
    "players": {"max": 20, "online": 0},
    "version": {"name": "1.8-pre1", "protocol": 44},
    "description": "A Minecraft Server",
    "enforcesSecureChat": True,
    "favicon": "data:image/png;base64,foo",
}

QUERY_RAW_RESPONSE = [
    {
        "hostname": "A Minecraft Server",
        "gametype": "GAME TYPE",
        "game_id": "GAME ID",
        "version": "1.8",
        "plugins": "",
        "map": "world",
        "numplayers": "3",
        "maxplayers": "20",
        "hostport": "9999",
        "hostip": "192.168.56.1",
    },
    ["Dinnerbone", "Djinnibone", "Steve"],
]

BEDROCK_RAW_RESPONSE = [
    "MCPE",
    "§r§4G§r§6a§r§ey§r§2B§r§1o§r§9w§r§ds§r§4e§r§6r",
    "422",
    "1.18.100500",
    "1",
    "69",
    "3767071975391053022",
    "map name here",
    "Default",
    "1",
    "19132",
    "-1",
    "3",
]

# NOTE: if updating this, be sure to change other occurrences of this help text!
# to update, use: `COLUMNS=100000 poetry run mcstatus --help`
EXPECTED_HELP_OUTPUT = """
usage: mcstatus [-h] [--bedrock] address {ping,status,query,json} ...

mcstatus provides an easy way to query 1.7 or newer Minecraft servers for any information they can expose. It provides three modes of access: query, status, ping and json.

positional arguments:
  address               The address of the server.

options:
  -h, --help            show this help message and exit
  --bedrock             Specifies that 'address' is a Bedrock server (default: Java).

commands:
  Command to run, defaults to 'status'.

  {ping,status,query,json}
    ping                Ping server for latency.
    status              Prints server status.
    query               Prints detailed server information. Must be enabled in servers' server.properties file.
    json                Prints server status and query in json.
"""  # noqa: E501 (line length)


@contextlib.contextmanager
def patch_stdout_stderr():
    outpatch = patch("sys.stdout", new=io.StringIO())
    errpatch = patch("sys.stderr", new=io.StringIO())
    with outpatch as out, errpatch as err:
        yield out, err


@pytest.fixture
def mock_network_requests():
    with \
        patch("mcstatus.server.JavaServer.lookup", return_value=JavaServer("example.com", port=25565)), \
        patch("mcstatus.server.JavaServer.ping", return_value=0), \
        patch("mcstatus.server.JavaServer.status", return_value=JavaStatusResponse.build(JAVA_RAW_RESPONSE)), \
        patch("mcstatus.server.JavaServer.query", return_value=QueryResponse.build(*QUERY_RAW_RESPONSE)), \
        patch("mcstatus.server.BedrockServer.lookup", return_value=BedrockServer("example.com", port=25565)), \
        patch("mcstatus.server.BedrockServer.status", return_value=(
            BedrockStatusResponse.build(BEDROCK_RAW_RESPONSE, latency=123)
        )
    ):  # fmt: skip # multiline with was added in Python 3.10
        yield


def normalise_help_output(s: str) -> str:
    """
    Normalises the output of `mcstatus --help`, to work around
    some discrepancies between Python versions while still retaining
    meaningful information for comparison.
    """

    elided = "[...]:"

    s = s.strip()

    # drop lines which end in ":". these argparse section headings vary between python versions.
    # it is just a small style change, so it doesn't matter so much to do `sys.version_info` check
    return "\n".join(ln if not ln.endswith(":") else elided for ln in s.splitlines())


# NOTE: for premature exits in argparse, we must catch SystemExit.
# for ordinary exits in the CLI code, we can simply inspect the return value.


def test_no_args():
    with patch_stdout_stderr() as (out, err), pytest.raises(SystemExit) as exn:
        main_under_test([])

    assert out.getvalue() == ""
    assert "usage: " in err.getvalue()
    assert exn.value.code != 0


def test_help():
    with patch_stdout_stderr() as (out, err), pytest.raises(SystemExit) as exn:
        main_under_test(["--help"])

    assert "usage: " in out.getvalue()
    assert err.getvalue() == ""
    assert exn.value.code == 0


@mock.patch.dict(os.environ, {"COLUMNS": "100000"})  # prevent line-wrapping in --help output
def test_help_matches_recorded_output():
    with patch_stdout_stderr() as (out, err), pytest.raises(SystemExit):
        main_under_test(["--help"])

    assert normalise_help_output(out.getvalue()) == normalise_help_output(EXPECTED_HELP_OUTPUT)
    assert err.getvalue() == ""


def test_one_argument_is_status(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com"]) == 0

    assert (
        "version: Java 1.8-pre1 (protocol 44)\n"
        "motd: \x1b[0mA Minecraft Server\x1b[0m\n"
        "players: 0/20 No players online\n"
        "ping: 0.00 ms\n"
    ) == out.getvalue()
    assert err.getvalue() == ""


def test_status(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com", "status"]) == 0

    assert (
        "version: Java 1.8-pre1 (protocol 44)\n"
        "motd: \x1b[0mA Minecraft Server\x1b[0m\n"
        "players: 0/20 No players online\n"
        "ping: 0.00 ms\n"
    ) == out.getvalue()
    assert err.getvalue() == ""


def test_status_bedrock(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com", "--bedrock", "status"]) == 0

    assert (
        "version: Bedrock 1.18.100500 (protocol 422)\n"
        "motd: \x1b[0m\x1b[0m\x1b[0m\x1b[38;2;170;0;0mG\x1b[0m\x1b[0m\x1b[38;2;255;170;0ma\x1b[0m\x1b[0m\x1b[38;2;255;255;85m"
        "y\x1b[0m\x1b[0m\x1b[38;2;0;170;0mB\x1b[0m\x1b[0m\x1b[38;2;0;0;170mo\x1b[0m\x1b[0m\x1b[38;2;85;85;255mw\x1b[0m\x1b[0m"
        "\x1b[38;2;255;85;255ms\x1b[0m\x1b[0m\x1b[38;2;170;0;0me\x1b[0m\x1b[0m\x1b[38;2;255;170;0mr\x1b[0m\n"
        "players: 1/69\n"
        "ping: 123.00 ms\n"
    ) == out.getvalue()
    assert err.getvalue() == ""


def test_status_offline(mock_network_requests):
    with patch_stdout_stderr() as (out, err), patch("mcstatus.server.JavaServer.status", side_effect=TimeoutError):
        assert main_under_test(["example.com", "status"]) == 1

    assert out.getvalue() == ""
    assert err.getvalue() == "Error: TimeoutError()\n"


def test_query(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com", "query"]) == 0

    assert (
        "host: 192.168.56.1:9999\n"
        "software: Java 1.8 vanilla\n"
        "motd: \x1b[0mA Minecraft Server\x1b[0m\n"
        "plugins: []\n"
        "players: 3/20 ['Dinnerbone', 'Djinnibone', 'Steve']\n"
    ) == out.getvalue()
    assert err.getvalue() == ""


def test_query_offline(mock_network_requests):
    with patch_stdout_stderr() as (out, err), patch("mcstatus.server.JavaServer.query", side_effect=socket.timeout):
        assert main_under_test(["example.com", "query"]) != 0

    assert out.getvalue() == ""
    assert err.getvalue() == QUERY_FAIL_WARNING + "\n"


def test_json(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com", "json"]) == 0

    data = json.loads(out.getvalue())
    assert data == {
        "online": True,
        "kind": "Java",
        "status": {
            "players": {"online": 0, "max": 20, "sample": None},
            "version": {"name": "1.8-pre1", "protocol": 44},
            "motd": "A Minecraft Server",
            "latency": 0,
            "raw": {
                "players": {"max": 20, "online": 0},
                "version": {"name": "1.8-pre1", "protocol": 44},
                "description": "A Minecraft Server",
                "enforcesSecureChat": True,
                "favicon": "data:image/png;base64,foo",
            },
            "enforces_secure_chat": True,
            "icon": "data:image/png;base64,foo",
            "forge_data": None,
        },
        "query": {
            "ip": "192.168.56.1",
            "port": "9999",
            "map": "world",
            "plugins": [],
            "raw": {
                "hostname": "A Minecraft Server",
                "gametype": "GAME TYPE",
                "game_id": "GAME ID",
                "version": "1.8",
                "plugins": "",
                "map": "world",
                "numplayers": "3",
                "maxplayers": "20",
                "hostport": "9999",
                "hostip": "192.168.56.1",
            },
        },
    }
    assert err.getvalue() == ""


def test_ping(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com", "ping"]) == 0

    assert float(out.getvalue()) == 0
    assert err.getvalue() == ""


def test_ping_bedrock(mock_network_requests):
    with patch_stdout_stderr() as (out, err):
        assert main_under_test(["example.com", "--bedrock", "ping"]) == 0

    assert float(out.getvalue()) == 123
    assert err.getvalue() == ""


def test_ping_server_doesnt_support(mock_network_requests):
    with patch_stdout_stderr() as (out, err), patch("mcstatus.server.JavaServer.ping", side_effect=TimeoutError("timeout")):
        assert main_under_test(["example.com", "ping"]) == 0

    assert float(out.getvalue()) == 0
    assert err.getvalue() == PING_PACKET_FAIL_WARNING.format(address="example.com:25565", ping_exc="timeout") + "\n"
