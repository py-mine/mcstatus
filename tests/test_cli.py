import io
import os
import json
import contextlib
from unittest import mock, skip
from unittest.mock import patch
from pytest import raises

from mcstatus.__main__ import main as main_under_test

DEMO_SERVER = "demo.mcstatus.io"

# XXX: if updating this, be sure to change other occurences of this help text!
# to update, use: `COLUMNS=1000 poetry run mcstatus --help`
EXPECTED_HELP_OUTPUT = """
usage: mcstatus [-h] [--bedrock] address {ping,status,query,json} ...

mcstatus provides an easy way to query Minecraft servers for any information they can expose. It provides three modes of access: query, status, ping and json.

positional arguments:
  address               The address of the server.

options:
  -h, --help            show this help message and exit
  --bedrock             Specifies that 'address' is a Bedrock server (default: Java).

commands:
  Command to run, defaults to 'status'.

  {ping,status,query,json}
    ping                Ping server for latency.
    status              Prints server status. Supported by all Minecraft servers that are version 1.7 or higher.
    query               Prints detailed server information. Must be enabled in servers' server.properties file.
    json                Prints server status and query in json. Supported by all Minecraft servers that are version 1.7 or higher.
"""  # noqa: E501(line length)


@contextlib.contextmanager
def patch_stdout_stderr():
    outpatch = patch("sys.stdout", new=io.StringIO())
    errpatch = patch("sys.stderr", new=io.StringIO())
    with outpatch as out, errpatch as err:
        yield out, err


def normalise_help_output(s: str) -> str:
    """
    Normalises the output of `mcstatus --help`, to work around
    some discrepancies between Python versions while still retaining
    meaningful information for comparison.
    """

    elided = "[...]:"

    s = s.strip()

    # drop lines which end in ":". these argparse section headings vary between python versions.
    return "\n".join(ln if not ln.endswith(":") else elided for ln in s.splitlines())


# NOTE: for premature exits in argparse, we must catch SystemExit.
# for ordinary exits in the CLI code, we can simply inspect the return value.


def test_no_args():
    with patch_stdout_stderr() as (out, _), raises(SystemExit) as exn:
        main_under_test([])

    assert out.getvalue() == ""
    assert exn.value.code != 0


def test_help():
    with patch_stdout_stderr() as (out, err), raises(SystemExit) as exn:
        main_under_test(["--help"])

    assert "usage: " in out.getvalue()
    assert err.getvalue() == ""
    assert exn.value.code == 0


@mock.patch.dict(os.environ, {"COLUMNS": "100000"})  # prevent line-wrapping in --help output
def test_help_matches_recorded_output():
    with patch_stdout_stderr() as (out, err), raises(SystemExit):
        main_under_test(["--help"])

    assert normalise_help_output(out.getvalue()) == normalise_help_output(EXPECTED_HELP_OUTPUT)
    assert err.getvalue() == ""


def test_one_argument_is_status():
    with patch_stdout_stderr() as (out, err):
        assert main_under_test([DEMO_SERVER]) == 0

    assert "version:" in out.getvalue() and "players:" in out.getvalue()
    assert err.getvalue() == ""


def test_status():
    with patch_stdout_stderr() as (out, err):
        assert main_under_test([DEMO_SERVER, "status"]) == 0

    assert "version:" in out.getvalue() and "players:" in out.getvalue()
    assert "java" in out.getvalue().lower()
    assert err.getvalue() == ""


def test_status_bedrock():
    with patch_stdout_stderr() as (out, err):
        assert main_under_test([DEMO_SERVER, "--bedrock", "status"]) == 0

    assert "version:" in out.getvalue() and "players:" in out.getvalue()
    assert "bedrock" in out.getvalue().lower()
    assert err.getvalue() == ""


@skip("demo.mcstatus.io erroneously rejects our query packets. see: https://github.com/mcstatus-io/demo-server/issues/1")
def test_query():
    with patch_stdout_stderr() as (out, err):
        assert main_under_test([DEMO_SERVER, "query"]) == 0

    assert "plugins:" in out.getvalue() and "players:" in out.getvalue()
    assert err.getvalue() == ""


def test_json():
    with patch_stdout_stderr() as (out, err):
        assert main_under_test([DEMO_SERVER, "json"]) == 0

    assert err.getvalue() == ""
    data = json.loads(out.getvalue())
    assert data["online"]
    assert "status" in data
    # TODO: broken for same reason as test_query()
    # assert "query" in data


def test_ping():
    with patch_stdout_stderr() as (out, err):
        assert main_under_test([DEMO_SERVER, "ping"]) == 0

    assert float(out.getvalue()) > 0

    # potentially, a warning will be printed to stderr due to:
    # https://github.com/py-mine/mcstatus/issues/850
    # assert err.getvalue() == ''
