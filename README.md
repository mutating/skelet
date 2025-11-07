<details>
  <summary>ⓘ</summary>

[![Downloads](https://static.pepy.tech/badge/skelet/month)](https://pepy.tech/project/skelet)
[![Downloads](https://static.pepy.tech/badge/skelet)](https://pepy.tech/project/skelet)
[![Coverage Status](https://coveralls.io/repos/github/pomponchik/skelet/badge.svg?branch=main)](https://coveralls.io/github/pomponchik/skelet?branch=main)
[![Lines of code](https://sloc.xyz/github/pomponchik/skelet/?category=code)](https://github.com/boyter/scc/)
[![Hits-of-Code](https://hitsofcode.com/github/pomponchik/skelet?branch=main&label=Hits-of-Code&exclude=docs/)](https://hitsofcode.com/github/pomponchik/skelet/view?branch=main)
[![Test-Package](https://github.com/pomponchik/skelet/actions/workflows/tests_and_coverage.yml/badge.svg)](https://github.com/pomponchik/skelet/actions/workflows/tests_and_coverage.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/skelet.svg)](https://pypi.python.org/pypi/skelet)
[![PyPI version](https://badge.fury.io/py/skelet.svg)](https://badge.fury.io/py/skelet)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/pomponchik/skelet)

</details>

![logo](https://raw.githubusercontent.com/pomponchik/skelet/develop/docs/assets/logo_8.svg)


Collect all the settings in one place

Promo ideas:
- Simple and elegant syntax
- Thread safety and rudimentary transactionality
- No metaclasses


## Table of contents

- [**Quick start**](#quick-start)
- [**Documenting fields**](#documenting-fields)
- [**Default values**](#default-values)
- [**Secret fields**](#secret-fields)
- [**Type checking**](#type-checking)
- [**Validation of values**](#validation-of-values)
- [**Conflicts between fields**](#conflicts-between-fields)
- [**Sources**](#sources)
  - [**Environment variables**](#environment-variables)
  - [**TOML files and pyproject.toml**](#toml-files-and-pyproject-toml)
  - [**JSON files**](#json-files)
  - [**YAML files**](#yaml-files)
  - [**Collecting sources**](#collecting-sources)
- [**Type conversion**](#type-conversion)
- [**Thread safety**](#thread-safety)
- [**Callbacks for changes**](#callbacks-for-changes)
- [**Read only fields**](#read-only-fields)



One object with a configuration for your project.

It's ready now:

- [x] Default values specified in the class
- [x] Values that are set during operation for class attributes
- [x] Read only fields
- [x] Typing support
- [x] Checking field names (prohibit underscores at the beginning)
- [x] Documenting fields
- [x] The ability to validate any fields
- [x] A separate mutex for each field
- [x] Secret fields
- [x] The ability to set a callback to change any of the field
- [x] The ability to turn-off thread safety for reads of certain field
- [x] Checking fields for conflicts
- [x] The specified sections in the `pyproject.toml` file
- [x] One or more separate `toml` files
- [x] `json` format support
- [x] `yaml` format support
- [x] Special classes for checking through types for belonging to sets of positive or natural numbers
- [x] Default factories
- [x] Converting values from one to another
- [x] The ability to share a single mutex into several fields
- [x] Subtraction of environment variables
- [x] Aliases support
- [x] Individual source lists for each field, with ellipsis support

To do:

- [ ] The ability to disable type checking for a class through class arguments
- [ ] Class inheritance support
- [ ] Reading parameters from the CLI
- [ ] Context manager like https://confz.readthedocs.io/en/latest/usage/context_manager.html

Links to add here:

- https://www.reddit.com/r/Python/comments/10zdidm/why_type_hinting_sucks/
