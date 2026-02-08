# Compatibility Shims

This directory holds compatibility shims for deprecated public modules.

These modules are not part of the main source tree. They are mapped into their
deprecated import paths during packaging via Hatchling `force-include` entries
in `pyproject.toml` for the sdist (wheels are built from the sdist).

Example:

```toml
[tool.hatch.build.targets.sdist.force-include]
"mcstatus/_compat/status_response.py" = "mcstatus/status_response.py"
```

This means that the build system will include these for us in the actual built
packages, without the files having to clutter the actual source tree of the
project, making development cleaner and less confusing. As an additional
benefit, it prevents us from accidentally importing these deprecated utils from
within mcstatus, as they will simply not be present.

> [!WARNING]
> This approach does mean that people using mcstatus directly through a git
> submodule or otherwise attempt to run the mcstatus code from it's direct
> source, rather than going through the proper python module installation will
> NOT be able to utilize these deprecations.
>
> This isn't really a supported method of utilizing mcstatus though, and people
> that do so should expect to face issues.
