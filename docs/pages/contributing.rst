Contributing
============

Setup
-----

.. code-block:: sh

   pipx install poetry
   pipx inject poetry poetry-dynamic-versioning
   poetry install --with=docs
   poetry run pre-commit install

In addition to those tools, you may also want to install plugins for your IDE that interact with flake8, pyright, and ruff.

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

Common development tasks
------------------------

.. code-block:: sh

   poetry shell  # Activates the poetry virtual environment to avoid `poetry run` in front of every command
   poe docs  # Renders documentation from docs/ folder
   poe format  # Executes automatic formatter for style consistency
   poe lint  # Executes linting tools that help increase code quality
   poe test  # Executes unit tests

Listing available tasks
-----------------------

.. code-block:: sh

   poe

Being fancy with tasks
----------------------

You may pass extra arguments to the underlying tasks. Here's an example that
tells the underlying ``pytest`` to execute only the query tests with maximum
verbosity.

.. code-block:: sh

   poe test -vvv -k TestQuery
