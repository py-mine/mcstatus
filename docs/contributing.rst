Contributing
============

Setup:

.. code-block:: sh

   pipx install poetry
   pipx inject poetry poetry-dynamic-versioning
   pipx install tox
   pipx inject tox tox-poetry
   poetry run pre-commit install
