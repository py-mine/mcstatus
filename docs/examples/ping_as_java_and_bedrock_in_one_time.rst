Ping as Java and as Bedrock in one time
=======================================

You can easily ping a server as a Java server and as a Bedrock server in one time.

.. literalinclude:: code/ping_as_java_and_bedrock_in_one_time.py

As you see in the code, ``status`` function returns :class:`~mcstatus.pinger.PingResponse` or
:class:`~mcstatus.bedrock_status.BedrockStatusResponse` object. You can use :func:`isinstance` checks to access
attributes that are only in one of the objects.

.. code-block:: python

    response = await status("hypixel.net")

    if isinstance(response, PingResponse):
        print(response.description)
    else:
        print(response.motd)
    # or
    print(response.description if isinstance(response, PingResponse) else response.motd)
    # or the same with variable
    motd = response.description if isinstance(response, PingResponse) else response.motd
    print(motd)
