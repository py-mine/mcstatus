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


Transformers
------------

These are basic transformers, that you can use to show a MOTD in different
places (like browser or even terminal). Here is an example on how to use them:

.. code-block:: python

    PlainTransformer().transform(status.motd.parsed)
    # or you can also use
    status.motd.to_plain()

But you should generally prefer :meth:`~mcstatus.motd.Motd.to_plain`,
:meth:`~mcstatus.motd.Motd.to_minecraft`, :meth:`~mcstatus.motd.Motd.to_html` or
:meth:`~mcstatus.motd.Motd.to_ansi`.

.. module:: mcstatus.motd.transformers
    :no-index:

    .. autoclass:: PlainTransformer

    .. autoclass:: MinecraftTransformer

    .. autoclass:: HtmlTransformer

    .. autoclass:: AnsiTransformer
