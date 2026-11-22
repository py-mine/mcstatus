Exceptions
==========

The :mod:`mcstatus.exceptions` module contains public exceptions raised by mcstatus.
Operations may also raise standard Python exceptions and exceptions from dependencies;
not every error inherits from :exc:`mcstatus.exceptions.McstatusError`.

The base class is intended to support improved error handling as mcstatus develops,
but is currently used only in limited cases. See `issue #692
<https://github.com/py-mine/mcstatus/issues/692>`_ for ongoing work to document
and improve the exceptions that mcstatus operations can raise.

.. automodule:: mcstatus.exceptions
    :members: McstatusError
    :show-inheritance:
