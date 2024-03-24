Internal Data
=============

This page contains some internal objects, classes, functions, etc. These **are not a part of the Public API** and
you **should not use them**, as we do not guarantee their backwards compatibility between different library
versions. They are only documented here for linkable reference to them.


.. autoclass:: mcstatus.pinger.ServerPinger
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.pinger.AsyncServerPinger
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.bedrock_status.BedrockServerStatus
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: mcstatus.address
    :members:
    :exclude-members: Address
    :undoc-members:
    :show-inheritance:

    .. autoclass:: Address
        :members:
        :undoc-members:
        :show-inheritance:

        .. attribute:: host
            :type: str
            :canonical: mcstatus.address.Address.host

            The hostname or IP address of the server. Is a part of Public API.

        .. attribute:: port
            :type: int
            :canonical: mcstatus.address.Address.port

            The port of the server. Is a part of Public API.

.. automodule:: mcstatus.dns
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: mcstatus.responses.BaseStatusResponse
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.responses.BaseStatusPlayers
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.responses.BaseStatusVersion
    :members:
    :undoc-members:
    :show-inheritance:
