Versioning Practices & Guarantees
=================================

This page explains what you can expect when upgrading mcstatus, and what
changes may occur in major, minor, and patch releases.

mcstatus follows the `Semantic Versioning <https://semver.org>`_ model in terms
of **versioning guarantees and expectations**, using the familiar
``MAJOR.MINOR.PATCH`` structure.

Internally and for distribution, mcstatus version numbers follow `PEP 440
<https://peps.python.org/pep-0440/>`_. This primarily affects the exact format
of pre-releases, post-releases, and development releases, but does not change
the meaning of major, minor, or patch version increments.

- **MAJOR**: incompatible (breaking) changes to the public API
- **MINOR**: backwards-compatible features and improvements
- **PATCH**: backwards-compatible bug fixes

What is "public API"?
---------------------

For mcstatus, the **public API** is defined by what is **documented in the
public API pages**.

- Anything documented under :doc:`/api/basic` and :doc:`/api/motd_parsing` is
  public API.
- Anything documented under :doc:`/api/internal` is **not** public API.
- Anything not documented at all is also **not** public API.
- Any module, package, attribute, or symbol whose name starts with an
  underscore (``_``) is considered internal and may change at any time.

Release types and guarantees
----------------------------

.. warning::

   **Bug fixes are generally not backported.**

   mcstatus primarily supports the **latest released version** of the library.
   Bugs are fixed only in that version, and fixes are not backported to older
   releases.

   This includes most bug fixes and the vast majority of security-related
   fixes. Backporting fixes significantly increases maintenance overhead and
   often requires maintaining multiple diverging code paths, which is not
   sustainable for this project.

   In exceptional cases, a truly critical issue may be addressed via a hotfix
   release. Such cases are rare and handled on a best-effort basis.

   If you rely on older versions of mcstatus, you may encounter bugs that will
   not be fixed unless you upgrade.

Patch releases (x.y.PATCH)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Patch releases contain:

- bug fixes
- documentation changes of any kind (e.g. new docs pages, or also changes to
  docstrings of some public API objects in the codebase)
- improvements that do not change the public API contract
- breaking changes in private API
- dependency updates (including major dependency updates), as long as the
  public contract of this library remains compatible
- changes in library's public API typing behavior (see see
  :ref:`typing-stability-guarantees`)

Patch releases do **not** contain breaking changes to the public API. They also
generally don't introduce any new behavior, other than for purposes of
resolving existing bugs, or internal updates.

Note that in some cases, if you are relying on behavior which we consider to be
a bug, it is possible that might end up changing this behavior in a PATCH
release, in an effort to fix the unintentional, wrong behavior, breaking your
dependency. Bug-fixes pretty much always happen without any deprecations.

.. admonition:: example

  To understand what constitutes a bug-fix with such breakage potential, as an
  example, if mcstatus incorrectly parses a MOTD format that some server sends,
  fixing that parsing is a bug fix, even if it changes the output format for
  that specific broken MOTD.

Another important note to mention is that mcstatus will not make any efforts to
delay its runtime dependency version updates to align them with minor or major
releases. Transitive breakages caused by dependency updates are considered
acceptable as long as mcstatus's documented public API remains compatible.

Minor releases (x.MINOR.z)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Generally, minor releases exist to introduce new features to the library in a
non-breaking way. They may include:

- new public features (new classes, functions, parameters, constants) without
  affecting existing behavior
- new optional arguments in public functions/class constructors with sensible
  defaults that don't change existing usage
- **new deprecations** (introduced as warnings containing new replacements /
  deprecation reasons)
- backwards-compatible behavior improvements
- dropping support for a python version (e.g. dropping python 3.9 because it is
  past it's end-of-life)
- any additional changes that patch releases can contain


Minor releases do **not** intentionally introduce breaking changes to the
documented public API.


Deprecations in minor releases
  New deprecations may be introduced in minor releases for behavior that is
  scheduled for removal in the next major version. These deprecations are
  emitted as warnings and do not immediately break existing code. For more
  information about our deprecation handling, see the
  :ref:`deprecations-and-removals` section.

Major releases (MAJOR.y.z)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Major releases may include breaking changes to the documented public API. These
will be called out in the changelog and typically include one or more of:

- removing a documented public class, function, or attribute
- renaming a public API without a deprecated alias
- changing the default value or meaning of a function parameter in a way that
  changes original usage
- removing a deprecated alias or deprecated import path
- any additional changes that minor and patch releases can contain

We generally try to avoid immediate breaking changes that didn't go through at
least a brief deprecation period of at least 1 release cycle (e.g. deprecation
will first be introduced in v12.4.0, before the old behavior is removed in
v13).

If a major refactor of the library was performed, or just generally one that is
expected to make a lot of our users to face deprecations, we try to introduce
these deprecations in a major release, instead of a minor one (with them
staying in the project until the next major release after this one). Though
this is not a guarantee.

We can still choose to not go through deprecations at all and introduce
entirely new breaking changes in a new major release. We will however try to
avoid doing so unless we have a very strong reason to do so.

mcstatus and Minecraft versions
-------------------------------

mcstatus is somewhat coupled to Minecraft server protocols and behaviors. As
Minecraft evolves, mcstatus may need to make changes that are "breaking" at the
library level, even if they are driven by protocol or ecosystem changes.

mcstatus aims to:

- remain compatible with widely used Minecraft versions and server
  implementations
- release updates in a timely manner when protocol behavior or common server
  responses change
- provide support for legacy Minecraft versions (within reason), if the latest
  protocol for obtaining status is no longer compatible with the previous one

Fortunately, breaking changes in the protocol when it comes to obtaining server
status are very uncommon. But it is possible that Minecraft introduces a change
that our library cannot process at the time of introduction, this might or
might not cause hard failures on mcstatus part, even if older Minecraft clients
can process these information, mcstatus might not be able to without us
releasing a new version to support it.

Because mcstatus is maintained by volunteers, timing may vary, but we try to
keep mcstatus working with the latest Minecraft releases and fix critical bugs
quickly.

.. _typing-stability-guarantees:

Typing stability guarantees
---------------------------

mcstatus is a strongly typed library which actively supports and encourages the
use of type-checkers.

However, typing definitions occasionally need to change alongside internal
refactors so that mcstatus itself remains internally type-correct, and Python's
typing system unfortunately does not really provide a practical way to
deprecate types gracefully.

For this reason, **typing breakages may occur even in patch releases**.

We actively try to avoid typing breakages or postpone them to minor or even
major releases when possible, but if doing so would significantly slow down our
ability to deliver a necessary bug-fix or feature, we do not consider
maintaining the stability of the public typing interface significant enough to
prevent us from shipping such a change.

.. admonition:: example

   To understand what we meant by breaking changes in the public typing
   interface, it can include things like:

   - Adding a ``@final`` decorator to one of our classes
   - Making a class generic
   - Introducing an additional type parameter to already generic class
   - Removing a generic type parameter / making a class no longer generic
   - Adding a convenience type-alias variable
   - Adding a new type into a union of types in an exposed convenience
     type-alias

   Any of these changes can occur even in a patch release.

.. _deprecations-and-removals:

Deprecations and removals
-------------------------

When we deprecate something, we aim to emit a ``DeprecationWarning`` with a
message containing:

- what was deprecated
- what to use instead (if a replacement is available)
- a target removal version

When we remove something, we generally aim to remove it in a **major release**,
after it has been deprecated for at least one release cycle. For some more
significant changes, we can sometimes keep a deprecation around for longer
though.

.. warning::

   **Relying on deprecated behavior after its removal is unsupported.**

   If you continue using deprecated functionality beyond its stated removal
   version, mcstatus does not guarantee that resulting errors will clearly
   indicate the original deprecation.

   After removal, failures may surface as generic errors such as
   ``AttributeError`` or similar runtime exceptions.

   In some cases, mcstatus may choose to keep deprecation handling in place and
   raise a ``DeprecationWarning`` as a hard exception instead of merely
   emitting a warning. This behavior is **not guaranteed**, may differ between
   features, and may be removed at any time, including in patch releases.

   For this reason, you should always pay attention to deprecation warnings and
   resolve them ahead of time, ideally after any minor updates, but at the very
   least before upgrading to a new major version, to avoid sudden unexpected
   hard breakages.
