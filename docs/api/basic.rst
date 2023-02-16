Basic Usage
===========

We are small package, so our API is not so big. There are only few classes, which are suggested for a basic usage.


Request Classes
---------------

These are classes, that you use to send a request to server.


.. autoclass:: mcstatus.server.MCServer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.server.JavaServer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.server.BedrockServer
    :members:
    :undoc-members:
    :show-inheritance:


Response Objects
----------------

These are the classes that you get back after making a request.

For Java Server
***************

.. module:: mcstatus.status_response

.. autoclass:: mcstatus.status_response.JavaStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.status_response.JavaStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.status_response.JavaStatusPlayer()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.status_response.JavaStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. module:: mcstatus.querier

.. class:: QueryResponse
    :canonical: mcstatus.querier.QueryResponse

    The response object for :meth:`JavaServer.query() <mcstatus.server.JavaServer.query>`.

    .. class:: Players
        :canonical: mcstatus.querier.QueryResponse.Players

        Class for storing information about players on the server.

        .. attribute:: online
            :type: int
            :canonical: mcstatus.querier.QueryResponse.Players.online

            The number of online players.

        .. attribute:: max
            :type: int
            :canonical: mcstatus.querier.QueryResponse.Players.max

            The maximum allowed number of players (server slots).

        .. attribute:: names
            :type: list[str]
            :canonical: mcstatus.querier.QueryResponse.Players.names

            The list of online players.

    .. class:: Software
        :canonical: mcstatus.querier.QueryResponse.Software

        Class for storing information about software on the server.

        .. attribute:: version
            :type: str
            :canonical: mcstatus.querier.QueryResponse.Software.version

            The version of the software.

        .. attribute:: brand
            :type: str
            :value: "vanilla"
            :canonical: mcstatus.querier.QueryResponse.Software.brand

            The brand of the software. Like `Paper <https://papermc.io>`_ or `Spigot <https://www.spigotmc.org>`_.

        .. attribute:: plugins
            :type: list[str]
            :canonical: mcstatus.querier.QueryResponse.Software.plugins

            The list of plugins. Can be empty if hidden.

    .. attribute:: motd
        :type: str
        :canonical: mcstatus.querier.QueryResponse.motd

        The MOTD of the server. Also known as description.

    .. attribute:: map
        :type: str
        :canonical: mcstatus.querier.QueryResponse.map

        The name of the map.

    .. attribute:: players
        :type: ~QueryResponse.Players
        :canonical: mcstatus.querier.QueryResponse.players

        The players information.

    .. attribute:: software
        :type: ~QueryResponse.Software
        :canonical: mcstatus.querier.QueryResponse.software

        The software information.


For Bedrock Servers
*******************

.. module:: mcstatus.status_response
    :noindex:

.. autoclass:: mcstatus.status_response.BedrockStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.status_response.BedrockStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.status_response.BedrockStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build


Conclusion
----------

That is all! See also our :doc:`examples </examples/examples>`!
