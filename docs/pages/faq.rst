Frequently Asked Question
=========================


Why doesn't :class:`~mcstatus.server.BedrockServer` have an async :meth:`~mcstatus.server.MCServer.lookup` method?
------------------------------------------------------------------------------------------------------------------

With Java servers, to find the server, we sometimes end up performing an SRV
DNS lookup. This means making a request to your DNS server and waiting for an
answer, making that lookup a blocking operation (during which other things can
be done).

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
    >>> query.motd
    'Ð\x9fÑ\x80Ð¸Ð²Ñ\x96Ñ\x82!'
    >>> query.motd.encode("iso-8859-1").decode("utf-8")
    'Привіт!'

:attr:`query.motd <mcstatus.querier.QueryResponse.motd>` here can be anything,
that contain incorrect encoding.


How to get server image?
------------------------

Bedrock servers do not provide icons, so you can't get server image from them.
For Java servers, you can use :attr:`status.favicon <mcstatus.pinger.PingResponse.favicon>`
attribute. It will return `Base64 <https://en.wikipedia.org/wiki/Base64>`_
encoded PNG image, so you can decode it in that way:

.. code-block:: python

    import base64

    with open("server-favicon.png", "wb") as server_favicon_file:
        server_favicon_file.write(base64.decodebytes(status.favicon))

.. note::
    Most modern browsers support pasting raw Base64 as image, without decoding it to file.

    See `How to display Base64 image <https://stackoverflow.com/questions/8499633>`_ and
    `Base64 Images: Support table <https://caniuse.com/atob-btoa>`_.
