Frequently Asked Questions
==========================


Why doesn't :class:`~mcstatus.server.BedrockServer` have an async :meth:`~mcstatus.server.MCServer.lookup` method?
------------------------------------------------------------------------------------------------------------------

With Java servers, to find the server, we sometimes end up performing an SRV
DNS lookup. This means making a request to your DNS server and waiting for an
answer, making that lookup a blocking operation (during which other things can
be done).

.. note::
    An SRV record allows the server to have an address like: ``hypixel.net``,
    that points to a some specified IP/Host and port, depending on this record.

    That way, even if the server is hosted on a non-standard port (other than
    25565, say 8855), you won't need to use ``myserver.com:8855``, since the
    port number will simply be stored in the SRV record, so people can still
    connect simply with ``myserver.com``.

    On top of that, it also allows to specify a different IP/Host, which means
    you don't need to use the same server to run both the website, and the
    minecraft server. Instead, the SRV record can simply point to a different
    IP/Host address (like ``mc.hypixel.net``, or ``209.222.114.112``).

However with Bedrock servers, no such lookups are required (Bedrock doesn't
support SRV records), and so there is no blocking I/O operation being made,
that would justify having an async version.

In fact, all that the bedrock lookup does is parsing the ``host:port`` address,
and obtaining the ``host`` and ``port`` parts out of it (with some error
handling, and support for default ports).


Incorrect encoding
------------------

In Query protocol, Minecraft uses ISO 8859-1 for encoding all text (like MOTD,
server name, etc.). This can cause problems with non-latin characters. To fix
such error, you can re-encode text into UTF-8.

.. code-block:: python

    >>> query = JavaServer.lookup("my-server-ip.com").query()
    >>> query.motd.to_minecraft()
    'Ð\x9fÑ\x80Ð¸Ð²Ñ\x96Ñ\x82!'
    >>> query.motd.to_minecraft().encode("iso-8859-1").decode("utf-8")
    'Привіт!'

:attr:`query.motd <mcstatus.querier.QueryResponse.motd>` here can be anything,
that contains incorrect encoding.


How to get server image?
------------------------

On Bedrock, only official servers have a server image. There is no way to get
or set an icon to a custom server. For Java servers, you can use
:attr:`status.icon <mcstatus.responses.JavaStatusResponse.icon>`
attribute. It will return `Base64 <https://en.wikipedia.org/wiki/Base64>`_
encoded PNG image. If you wish to save this image into a file, this is how:

.. code-block:: python

    import base64
    from mcstatus import JavaServer

    server = JavaServer.lookup("hypixel.net")
    status = server.status()

    decoded_icon = base64.b64decode(status.icon.removeprefix("data:image/png;base64,"))
    with open("server-icon.png", "wb") as f:
        f.write(decoded_icon)

.. note::
    Most modern browsers support simply pasting the raw Base64 image into the
    URL bar, which will open it as an image preview, allowing you to take a
    quick look at it without having to use file saving from Python.

    See `How to display Base64 image <https://stackoverflow.com/questions/8499633>`_
    and `Base64 Images: Support table <https://caniuse.com/atob-btoa>`_.
