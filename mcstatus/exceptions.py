from abc import ABC


class McstatusError(Exception, ABC):
    """Base exception class for any mcstatus managed errors.

    This exception base class is never raised directly, it is only used to define further
    exception classes within mcstatus.
    """

    def __init__(self, msg: str) -> None:
        self.msg: str = msg
        super().__init__(self.msg)
