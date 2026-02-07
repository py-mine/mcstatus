MOTD Parsing
============

We provide a really powerful system to parse servers MOTDs.


The main class
--------------

Firstly there is the main class, which you get directly from :meth:`status <mcstatus.server.MCStatus.status>` methods.

.. autoclass:: mcstatus.motd.Motd
    :members:
    :undoc-members:


Components
----------

Those are used in :attr:`~mcstatus.motd.Motd.parsed` field.

.. automodule:: mcstatus.motd.components
    :members:
    :undoc-members:

    .. py:type:: ParsedMotdComponent
      :canonical: Formatting | MinecraftColor | WebColor | TranslationTag | str
