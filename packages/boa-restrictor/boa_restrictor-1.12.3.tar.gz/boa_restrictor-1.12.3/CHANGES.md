# Changelog

**1.12.3** (2025-10-15)
  * Maintenance updates via ambient-package-update

**1.12.2** (2025-10-10)
  * Maintenance updates via ambient-package-update

**1.12.1** (2025-09-29)
  * Optimized toml variable loading

**1.12.0** (2025-09-29)
  * Reverted changes after finding **critical bug** leading to always skipping first file passed from pre-commit

**1.11.2** (2025-09-29)
  * Possible bugfix with pre-commit integration

**1.11.1** (2025-09-29)
  * Made linter more robust against unexpected issues

**1.11.0** (2025-09-29)
  * Added new `AvoidTupleBasedModelChoices` rule

**1.10.6** (2025-09-02)
  * Added `noqa` option to docs

**1.10.5** (2025-08-18)
  * Fixed an odd issue with rules not being detected

**1.10.4** (2025-08-15)
  * Fixed a bug which caused `DBR005` rule to crash on relative imports

**1.10.3** (2025-08-14)
  * Added disclaimer about linter usage to the docs

**1.10.2** (2025-07-09)
  * Extended PBR008 to also detect set and dict comprehensions

**1.10.1** (2025-07-08)
  * Extended PBR008 to also detect list comprehensions

**1.10.0** (2025-07-01)
  * Added Django-only rule to prohibit usage of "django.db" in the API layer (DBR005)

**1.9.0** (2025-06-28)
  * Added new rule to prohibit usage of loops in unittests (PBR008)

**1.8.1** (2025-06-11)
  * Improved docs and added test for file-based rule exclusions

**1.8.0** (2025-06-11)
  * Added rule to prohibit usage of "datetime.now()" in favour of "django.utils.timezone.now()"
  * Restructured documentation
  * Updated package claim to include Django

**1.7.3** (2025-05-29)
  * Maintenance updates via ambient-package-update

* *1.7.2* (2025-05-12)
    * Fixed a bug in the docs at "DBR002"

* *1.7.1* (2025-05-12)
    * Updated docs about ruff support and Django-based rules

* *1.7.0* (2025-05-09)
    * Avoid usage of type-hints in variable names as suffixes (PBR007)

* *1.6.0* (2025-05-09)
    * Added rule DBR003 to prohibit usage of "assertTrue" and "assertFalse" in Django unittests

* *1.5.3* (2025-05-09)
    * Fixed bug that DBR rules couldn't be ignored via "noqa" statements

* *1.5.2* (2025-05-09)
    * Removed matches of DBR002 if import is just for type-hinting purposes

* *1.5.1* (2025-04-16)
    * Fixed a bug which would show wrong occurrence paths in pre-commit output

* *1.5.0* (2025-04-16)
    * Added Django-only rule to prohibit usage of "django.db" in the view layer

* *1.4.0* (2025-04-11)
    * Added first Django-only rule to prohibit use of `TestCase.assertRaises()`

* *1.3.5* (2025-04-04)
    * Caught exception when pyproject.toml contains syntax errors

* *1.3.4* (2025-04-04)
    * Maintenance via ambient-package-update

* *1.3.3* (2025-01-15)
    * Fixed a crash when invalid source code was passed to the linter

* *1.3.2* (2025-01-15)
    * Moved parts of documentation from Readme to RTD

* *1.3.1* (2025-01-13)
    * Added check in unittests to avoid forgetting to register new rules

* *1.3.0* (2025-01-13)
    * Added rule `PBR005` for ensuring service classes have exactly one public method called "process"
    * Added rule `PBR006` for ensuring abstract classes inherit from `abc.ABC`

* *1.2.1* (2024-12-13)
    * Allowed other imports from `datetime` module except `datetime` and `date`

* *1.2.0* (2024-12-10)
    * Added per-file exclusion list in configuration
    * Added warnings if non-existing rules are excluded in the configuration
    * Removed occurrence counter output in CLI since `pre-commit` calls the linter recursively

* *1.1.2* (2024-12-09)
    * Removed success message since `pre-commit` runs any linter *x* times

* *1.1.1* (2024-12-09)
    * Fixed a bug that caused `PBR004` not to be executed

* *1.1.0* (2024-12-09)
    * Added rule `PBR003` for prohibiting import nested datetime from datetime module
    * Added rule `PBR004` for enforcing `kw_only` parameter for dataclasses
    * Moved AST creation from rule declaration to cli level for performance reasons

* *1.0.3* (2024-12-02)
    * Re-added Django dependency
    * Added ruff linting rules

* *1.0.2* (2024-12-02)
    * Fixed sphinx docs

* *1.0.1* (2024-12-02)
    * Added forgotten changelog
    * Added docs for git tags for pre-commit

* *1.0.0* (2024-12-02)
    * Added rule `PBR001` for enforcing kwargs in functions and methods
    * Added rule `PBR002` for enforcing return type-hints when a function contains a return statement
    * Project setup and configuration
