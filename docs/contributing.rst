Contributing
============

Setup
-----

.. code-block:: sh

   pipx install poetry
   pipx inject poetry poetry-dynamic-versioning
   pipx install tox
   pipx inject tox tox-poetry
   poetry run pre-commit install

In addition to those tools, you may also want to install flake8 and black
plugins for your IDE.

Expectations
------------

When making changes to code that results in new behavior, it is expected that
automated tests are submitted as well to prevent the behavior from breaking in
the future. It matters not whether those changes are for a bugfix or a new
feature; all behavior changes require tests.

Feel free to hop on the `Discord server <https://discord.gg/C2wX7zduxC>`_ to
chat with other maintainers if you are unsure about something. We would
definitely rather have a conversation first before consuming unnecessary time
for something that someone else could already be working on or any other reason
that might make the work unnecessary. It is a community effort to maintain and
grow mcstatus. Much discussion happens on the `Discord server
<https://discord.gg/C2wX7zduxC>`_ to collaborate ideas together.

Once you have all the checks passing and any new behavior changes are tested,
feel free to open a pull request. Pull requests are how GitHub allows forks to
submit branches for consideration to be merged into the original repo.

Running all the checks
----------------------

.. code-block:: sh

   tox

Running a specific list of checks
---------------------------------

.. code-block:: sh

   tox -e lint,py37,py38

Listing all the specific names that can be passed to ``-e``
-----------------------------------------------------------

.. code-block:: sh

   tox -a

Being fancy with pytest
-----------------------

Any options you want to pass directly to pytest can be done after a double dash ``--``:

.. code-block:: sh

   tox -e py37 -- -vvv -k TestQuery
