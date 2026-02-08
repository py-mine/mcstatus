Internal Data
=============

This page contains some internal objects, classes, functions, etc. These **are not a part of the Public API** and
you **should not use them**, as we do not guarantee their backwards compatibility between different library
versions. They are only documented here for linkable reference to them.


.. autoclass:: mcstatus._protocol.java_client.JavaClient
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus._protocol.java_client.AsyncJavaClient
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus._protocol.legacy_client.LegacyClient
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus._protocol.legacy_client.AsyncLegacyClient
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus._protocol.bedrock_client.BedrockClient
    :members:
    :undoc-members:
    :show-inheritance:

.. automodule:: mcstatus._net.address
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
            :canonical: mcstatus._net.address.Address.host

            The hostname or IP address of the server.

        .. attribute:: port
            :type: int
            :canonical: mcstatus._net.address.Address.port

            The port of the server.

.. automodule:: mcstatus._net.dns
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: mcstatus.responses.base.BaseStatusResponse
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.responses.base.BaseStatusPlayers
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.responses.base.BaseStatusVersion
    :members:
    :undoc-members:
    :show-inheritance:
