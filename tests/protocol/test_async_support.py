from inspect import iscoroutinefunction

from mcstatus._protocol.io.connection import TCPAsyncSocketConnection, UDPAsyncSocketConnection


def test_is_completely_asynchronous():
    conn = TCPAsyncSocketConnection
    assertions = 0
    for attribute in dir(conn):
        if attribute.startswith(("read_", "write_")):
            assert iscoroutinefunction(getattr(conn, attribute))
            assertions += 1
    assert assertions > 0, "No read_*/write_* attributes were found"


def test_query_is_completely_asynchronous():
    conn = UDPAsyncSocketConnection
    assertions = 0
    for attribute in dir(conn):
        if attribute.startswith(("read_", "write_")):
            assert iscoroutinefunction(getattr(conn, attribute))
            assertions += 1
    assert assertions > 0, "No read_*/write_* attributes were found"
