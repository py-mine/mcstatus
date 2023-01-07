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

.. module:: mcstatus.pinger

.. class:: PingResponse
    :canonical: mcstatus.pinger.PingResponse

    The response object for :meth:`JavaServer.status() <mcstatus.server.JavaServer.status>`.

    .. class:: Players
        :canonical: mcstatus.pinger.PingResponse.Players

        Class for storing information about players on the server.

        .. class:: Player
            :canonical: mcstatus.pinger.PingResponse.Players.Player

            Class with information about a single player.

            .. attribute:: name
                :type: str
                :canonical: mcstatus.pinger.PingResponse.Players.Player.name

                Name of the player.

            .. attribute:: id
                :type: str
                :canonical: mcstatus.pinger.PingResponse.Players.Player.id

                ID of the player (in `UUID <https://en.wikipedia.org/wiki/Universally_unique_identifier>`_ format).

        .. attribute:: online
            :type: int
            :canonical: mcstatus.pinger.PingResponse.Players.online

            Current number of online players.

        .. attribute:: max
            :type: int
            :canonical: mcstatus.pinger.PingResponse.Players.max

            The maximum allowed number of players (server slots).

        .. attribute:: sample
            :type: list[Player] | None
            :canonical: mcstatus.pinger.PingResponse.Players.sample

            List of players, who are online. If server didn't provide this, it will be :obj:`None`.

            Actually, this is what appears when you hover over the slot count on the multiplayer screen.

            .. note::
                It's often empty or even contains some advertisement, because the specific server implementations or
                plugins can disable providing this information or even change it to something custom.

                There is nothing that ``mcstatus`` can to do here if the player sample was modified/disabled like this.


    .. class:: Version
        :canonical: mcstatus.pinger.PingResponse.Version

        A class for storing version information.

        .. attribute:: name
            :type: str
            :canonical: mcstatus.pinger.PingResponse.Version.name

            The version name, like ``1.19.3``. See
            `Minecraft wiki <https://minecraft.fandom.com/wiki/Java_Edition_version_history#Full_release>`__
            for complete list.

        .. attribute:: protocol
            :type: int
            :canonical: mcstatus.pinger.PingResponse.Version.protocol

            The protocol version, like ``761``. See
            `Minecraft wiki <https://minecraft.fandom.com/wiki/Protocol_version#Java_Edition_2>`__.

    .. attribute:: latency
        :type: float
        :canonical: mcstatus.pinger.PingResponse.latency

        The latency between you and the server in milliseconds.

    .. attribute:: players
        :type: ~PingResponse.Players
        :canonical: mcstatus.pinger.PingResponse.players

        The players information.

    .. attribute:: version
        :type: ~PingResponse.Version
        :canonical: mcstatus.pinger.PingResponse.version

        The version information.

    .. attribute:: description
        :type: str
        :canonical: mcstatus.pinger.PingResponse.description

        The description of the server. Also known as MOTD.

    .. attribute:: favicon
        :type: str
        :canonical: mcstatus.pinger.PingResponse.favicon

        The favicon of the server. In `Base64 <https://en.wikipedia.org/wiki/Base64>`_ encoded PNG image format.

        .. todo: in FAQ will be an example how to convert it to an image. We need to link it here.

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

.. module:: mcstatus.bedrock_status

.. class:: BedrockStatusResponse
    :canonical: mcstatus.bedrock_status.BedrockStatusResponse

    The response object for :meth:`BedrockServer.status() <mcstatus.server.BedrockServer.status>`.

    .. class:: Version
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.Version

        A class for storing version information.

        .. attribute:: protocol
            :type: int
            :canonical: mcstatus.bedrock_status.BedrockStatusResponse.Version.protocol

            The protocol version, like ``565``. See
            `Minecraft wiki <https://minecraft.fandom.com/wiki/Protocol_version#Bedrock_Edition_2>`__.

        .. attribute:: brand
            :type: str
            :canonical: mcstatus.bedrock_status.BedrockStatusResponse.Version.brand

            ``MCPE`` or ``MCEE`` for Education Edition.

        .. attribute:: version
            :type: str
            :canonical: mcstatus.bedrock_status.BedrockStatusResponse.Version.version

            The version name, like ``1.19.60``. See
            `Minecraft wiki <https://minecraft.fandom.com/wiki/Bedrock_Edition_version_history#Bedrock_Edition>`__
            for complete list.


    .. attribute:: version
        :type: ~BedrockStatusResponse.Version
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.version

        The version information.

    .. attribute:: latency
        :type: float
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.latency

        The latency between you and the server in milliseconds.

    .. attribute:: players_online
        :type: int
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.players_online

        The number of online players.

    .. attribute:: players_max
        :type: int
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.players_max

        The maximum allowed number of players (server slots).

    .. attribute:: motd
        :type: str
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.motd

        The MOTD of the server. Also known as description.

    .. attribute:: map
        :type: str
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.map

        The name of the map.

    .. attribute:: gamemode
        :type: str
        :canonical: mcstatus.bedrock_status.BedrockStatusResponse.gamemode

        The name of the gamemode on the server.


Conclusion
----------

That is all! At least for general usage, if you want to use more advanced features, you can read :doc:`/api/advanced/index`.
