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

.. module:: mcstatus.responses

.. autoclass:: mcstatus.responses.JavaStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.JavaStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.JavaStatusPlayer()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.JavaStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.QueryResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.QueryPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.QuerySoftware()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build


For Bedrock Servers
*******************

.. module:: mcstatus.responses
    :no-index:

.. autoclass:: mcstatus.responses.BedrockStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.BedrockStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.BedrockStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build


Conclusion
----------

That is all! See also our :doc:`examples </examples/examples>`!
