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


Transformers
------------

These are basic transformers, that you can use to show a MOTD in different places (like browser or even terminal).

.. automodule:: mcstatus.motd.transformers
    :members:
    :undoc-members:
    :private-members:
    :exclude-members: HtmlTransformer, AnsiTransformer, _abc_impl

        .. autoclass:: HtmlTransformer
            :members:
            :undoc-members:
            :private-members:
            :exclude-members: _abc_impl, FORMATTING_TO_HTML_TAGS, MINECRAFT_COLOR_TO_RGB_BEDROCK, MINECRAFT_COLOR_TO_RGB_JAVA

        .. autoclass:: AnsiTransformer
            :members:
            :undoc-members:
            :private-members:
            :exclude-members: _abc_impl, FORMATTING_TO_ANSI_TAGS, MINECRAFT_COLOR_TO_RGB
