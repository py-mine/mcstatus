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

.. autoclass:: mcstatus.server.BaseJavaServer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.server.JavaServer
    :members:
    :undoc-members:
    :show-inheritance:

.. autoclass:: mcstatus.server.LegacyServer
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

For Java Server (1.7+)
**********************

.. module:: mcstatus.responses.java

.. autoclass:: mcstatus.responses.java.JavaStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.java.JavaStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.java.JavaStatusPlayer()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.java.JavaStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. module:: mcstatus.responses.query
    :no-index:

.. autoclass:: mcstatus.responses.query.QueryResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.query.QueryPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.query.QuerySoftware()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

Forge Data
**********

Forge mod metadata is available on :attr:`status.forge_data <mcstatus.responses.java.JavaStatusResponse.forge_data>`.

.. module:: mcstatus.responses.forge
    :no-index:

.. autoclass:: mcstatus.responses.forge.ForgeData()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.forge.ForgeDataChannel()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build, decode

.. autoclass:: mcstatus.responses.forge.ForgeDataMod()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build, decode

For Java Server (1.4-1.6)
*************************

.. versionadded:: 12.1.0

.. module:: mcstatus.responses.legacy
    :no-index:

.. autoclass:: mcstatus.responses.legacy.LegacyStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.legacy.LegacyStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.legacy.LegacyStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build


For Bedrock Servers
*******************

.. module:: mcstatus.responses.bedrock
    :no-index:

.. autoclass:: mcstatus.responses.bedrock.BedrockStatusResponse()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.bedrock.BedrockStatusPlayers()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build

.. autoclass:: mcstatus.responses.bedrock.BedrockStatusVersion()
    :members:
    :undoc-members:
    :inherited-members:
    :exclude-members: build


Conclusion
----------

That is all! See also our :doc:`examples </examples/examples>`!
