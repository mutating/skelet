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


Collect all the settings of your project in one place, ensure type safety, thread safety and information security, and automatically validate all types and values. Use a simple and elegant "pythonic" syntax. Automatically load values from config files and environment variables.

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


## Quick start

Install it:

```bash
pip install skelet
```

You can also quickly try out this and other packages without having to install using [instld](https://github.com/pomponchik/instld).

Now let's create our first storage class:

```python
from skelet import Storage, Field, NonNegativeInt

class ManDescription(Storage):
    name: str = Field('*')
    age: NonNegativeInt = Field(0, validation={'You must be 18 or older to feel important': lambda x: x >= 18}, validate_default=False)
```

You can immediately notice that this is very similar to dataclasses or models from Pydantic. Yes, it's very similar, but it's better sharpened specifically for use for storing settings.

So, let's create an object of our class and look at it:

```python
description = ManDescription(name='Evgeniy', age=32)
print(description)
#> ManDescription(name='Evgeniy', age=32)
```

The object that we created is not just a storage for several fields. It can also validate values and verify typing. Let's try to slip to it something wrong:

```python
description.age = -5
#> TypeError: The value "-5" (int) of the "age" field does not match the type NonNegativeInt.
description.age = 5
#> ValueError: You must be 18 or older to feel important
description.name = 3.14
#> TypeError: The value "3.14" (float) of the "name" field does not match the type str.
```

That's not bad! But you will become a real master of storing settings when you read the entire text below.


## Documenting fields

Sometimes, in order not to forget what a particular field in the repository means, you may be tempted to accompany it with a comment:

```python
class TheSecretFormula(Storage):
    the_secret_ingredient: str = Field('*')  # frogs' paws or something else nasty
    ...
```

Don't do that! It is better to use the `doc` parameter in the field:

```python
class TheSecretFormula(Storage):
    the_secret_ingredient: str = Field('*', doc="frogs' paws or something else nasty")
    ...
```

Not only does this make the code self-documenting, you will also receive "free" reminders of the contents of this field in all exceptions that the library will raise:

```python
formula = TheSecretFormula(the_secret_ingredient=13)
#> TypeError: The value "13" (int) of the "the_secret_ingredient" field (frogs' paws or something else nasty) does not match the type str.
```

## Default values

You must specify a default value for each field. It will be used until you somehow redefine it, or if no other value is found in the data sources.

There are 2 types of default values:

- **Ordinary**.
- **Lazy**, or delayed.

You can already see examples of ordinary default values above. Here's another one:

```python
class UnremarkableSettingsStorage(Storage):
    ordinary_field: str = Field('I am the ordinary default value!')

print(UnremarkableSettingsStorage())
#> UnremarkableSettingsStorage(ordinary_field='I am the ordinary default value!')
```

But you can also pass a function that returns the default value: it will be called every time a new object is created. This is called a lazy default value:

```python
class UnremarkableSettingsStorage(Storage):
    ordinary_field: str = Field(default_factory=lambda: 'I am the lazy default value!')

print(UnremarkableSettingsStorage())
#> UnremarkableSettingsStorage(ordinary_field='I am the lazy default value!')
```

This option is preferable if you want to use a mutable object, such as a `list` or `dict`, as the default value. A new object will be created for this field every time a new storage object is created, so your data will not be "shuffled".


## Secret fields

Sometimes it is better not to see the contents of some fields to strangers. If such people can read, for example, the logs of your program, you may have problems. Secret fields have been invented for such cases:

```python
class TopStateSecrets(Storage):
    who_killed_kennedy: str = Field('aliens', validation=lambda x: x != 'russians', secret=True)
    red_buttons_password: str = Field('1234', secret=True)

print(TopStateSecrets())
#> TopStateSecret(who_killed_kennedy=***, red_buttons_password=***)
```
If you mark a field with the `secret` flag, as in this example, its contents will be hidden not only when printing, but also under any exceptions that the library will raise:

```python
secrets = TopStateSecrets()

secrets.who_killed_kennedy = 'russians'
#> ValueError: The value *** (str) of the "who_killed_kennedy" field does not match the validation.
```

In all other respects, "secret" fields behave the same as regular ones, you can read values and write new ones.













































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

- [ ] The ability to not assign default values in any way
- [ ] The ability to disable type checking for a class through class arguments
- [ ] Class inheritance support
- [ ] Reading parameters from the CLI
- [ ] Context manager like https://confz.readthedocs.io/en/latest/usage/context_manager.html

Links to add here:

- https://www.reddit.com/r/Python/comments/10zdidm/why_type_hinting_sucks/

Promo ideas:
- 🐍 Simple and elegant "pythonic" syntax
- ⇆ Thread safety and rudimentary transactionality
- ⛓️‍💥 No metaclasses
