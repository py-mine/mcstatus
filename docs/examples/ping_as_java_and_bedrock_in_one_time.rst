Ping as Java and as Bedrock in one time
=======================================

You can easily ping a server as a Java server and as a Bedrock server in one time.

.. literalinclude:: code/ping_as_java_and_bedrock_in_one_time.py

As you can see in the code, ``status`` function returns :class:`~mcstatus.responses.JavaStatusResponse`
or :class:`~mcstatus.responses.BedrockStatusResponse` object. You can use
:func:`isinstance` checks to access attributes that are only in one of the
objects.

.. code-block:: python

    response = await status("hypixel.net")

    if isinstance(response, BedrockStatusResponse):
        map_name = response.map_name
    else:
        map_name = None
    # or
    map_name = response.map_name if isinstance(response, BedrockStatusResponse) else None

    print(f"Server map name is: {map_name}")
