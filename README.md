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


Collect all the settings of your project in one place. Ensure type safety, thread safety and information security, and automatically validate all types and values. Use simple and elegant "pythonic" syntax. Automatically load values from config files and environment variables.

## Table of contents

- [**Quick start**](#quick-start)
- [**Default values**](#default-values)
- [**Documenting fields**](#documenting-fields)
- [**Secret fields**](#secret-fields)
- [**Type checking**](#type-checking)
- [**Validation of values**](#validation-of-values)
- [**Conflicts between fields**](#conflicts-between-fields)
- [**Sources**](#sources)
  - [**Environment variables**](#environment-variables)
  - [**TOML files and pyproject.toml**](#toml-files-and-pyprojecttoml)
  - [**JSON files**](#json-files)
  - [**YAML files**](#yaml-files)
  - [**CLI interfaces**](#cli-interfaces)
  - [**Collecting sources**](#collecting-sources)
- [**Converting values**](#converting-values)
- [**Thread safety**](#thread-safety)
- [**Callbacks for changes**](#callbacks-for-changes)
- [**Read only fields**](#read-only-fields)
- [**Transformations and serialization**](#transformations-and-serialization)


## Quick start

Install it:

```bash
pip install skelet
```

You can also quickly try out this and other packages without having to install using [instld](https://github.com/pomponchik/instld).

Now let's create our first storage class. To do this, we need to inherit from the base class `Storage` and attach several fields to it — objects of the `Field` class:

```python
from skelet import Storage, Field, NonNegativeInt

class ManDescription(Storage):
    name: str = Field()
    age: NonNegativeInt = Field(validation={'You must be 18 or older to feel important': lambda x: x >= 18})
```

You can immediately notice that this is very similar to [dataclasses](https://docs.python.org/3/library/dataclasses.html) or [models from Pydantic](https://docs.pydantic.dev/latest/api/base_model/). Yes, it's very similar, but it's better sharpened specifically for use for storing settings.

So, let's create an object of our class and look at it:

```python
description = ManDescription(name='Evgeniy', age=32)
print(description)
#> ManDescription(name='Evgeniy', age=32)
```

The object that we created is not just a storage for several fields. It can also [validate values](#validation-of-values) and [verify typing](#type-checking). Let's try to slip to it something wrong:

```python
description.age = -5
#> TypeError: The value -5 (int) of the "age" field does not match the type NonNegativeInt.
description.age = 5
#> ValueError: You must be 18 or older to feel important
description.name = 3.14
#> TypeError: The value 3.14 (float) of the "name" field does not match the type str.
```

That's not bad! But you will become a real master of storing settings when you read the entire text below.


## Default values

The default value is used, you know, when there is no other data source to fill in the field. It will be used until you somehow redefine it, or if no other value is found in the [data sources](#sources).

You may not define a default value, but in this case you need to pass these values when creating the storage object. If you do set a default value, there are 2 ways to do this:

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


## Documenting fields

Sometimes, in order not to forget what a particular field in the repository means, you may be tempted to accompany it with a comment:

```python
class TheSecretFormula(Storage):
    the_secret_ingredient: str = Field()  # frogs' paws or something else nasty
    ...
```

Don't do that! It is better to use the `doc` parameter in the field:

```python
class TheSecretFormula(Storage):
    the_secret_ingredient: str = Field(doc="frogs' paws or something else nasty")
    ...
```

Not only does this make the code self-documenting, you will also receive "free" reminders of the contents of this field in all exceptions that the library will raise:

```python
formula = TheSecretFormula(the_secret_ingredient=13)
#> TypeError: The value 13 (int) of the "the_secret_ingredient" field (frogs' paws or something else nasty) does not match the type str.
```


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


## Type checking

You can specify a type hint for each field of your class. This is not necessary, but if you do, all values of this field will be automatically checked against the specified type, and if they do not match, a `TypeError` exception will be raised:

```python
class HumanMeasurements(Storage):
    number_of_legs: int = Field(2)
    number_of_hands: int = Field(2)

measurements = HumanMeasurements()

measurements.number_of_legs = 'two'
#> TypeError: The value 'two' (str) of the "number_of_legs" field does not match the type int.
```

The Python typing system has its limitations. According to the author, it is [too overcomplicated](https://www.reddit.com/r/Python/comments/10zdidm/why_type_hinting_sucks/), there are too many different concepts in it, and checking some of the type constraints in runtime is almost impossible. Therefore, the library supports only a subset of types from the typing module.

*How does it work?* It is based on a simple type matching check via `isinstance`. A minimum number of additional annotations is also supported:

- `Any` - means the same thing as the absence of an annotation.
- `Union` (in the old style or in the new one, using the `|` operator) - means logical OR between types.
- `Optional` (again, both in the old style and in the new one - via `|`) - means that a value of the specified type is expected, or `None`.
- `Lists`, `dicts`, and `tuples` can be specified with the types they contain. By default, the contents of these containers are not checked, but this is done in relation to external [sources](#sources).

The author deliberately does not try to implement full type checking in runtime. If you need more powerful verification, it's better to rely on static tools like `mypy`.

The library also supports 2 additional types that allow you to narrow down the behavior of the basic int type:

- `NaturalNumber` — as the name implies, only objects of type `int` greater than zero will be checked for this type.
- `NonNegativeInt` — the same as `NaturalNumber`, but `0` is also a valid value.

Please note that these types of constraints are checked only in runtime.


## Validation of values

In addition to type checking, you can specify arbitrary conditions by which field values will be checked.

The simplest way to validate a specific field is to pass a lambda function that returns a `bool` value as the `validation` argument for the field:

```python
class ScaryNumbers(Storage):
    unlucky_number: int = Field(13, validation=lambda x: x in [13, 17, 4, 9, 40], doc='a number that is considered unlucky by a particular people')
    number_of_the_beast: int = Field(666, validation=lambda x: x in [616, 666], doc='different translations of the Bible give different numbers for the beast')

numbers = ScaryNumbers()
```

This function should return `True` if the value is valid, and `False` if it is not. If you try to assign an invalid value to the field, an exception will be raised:

```python
numbers.unlucky_number = 7
#> ValueError: The value 7 (int) of the "unlucky_number" field (a number that is considered unlucky by a particular people) does not match the validation.
numbers.number_of_the_beast = 555
#> ValueError: The value 555 (int) of the "number_of_the_beast" field (different translations of the Bible give different numbers for the beast) does not match the validation.
```

You can also pass a dictionary as a `validation` parameter, where the keys are messages that will accompany the raised exceptions, and the values are the same functions that return boolean values:

```python
class Numbers(Storage):
    zero: int = Field(0, validation={'Zero is definitely greater than your value.': lambda x: x > -1, 'Zero is definitely less than your value.': lambda x: x < 1})
    ...

numbers = Numbers()

numbers.zero = 1
#> ValueError: Zero is definitely less than your value.
numbers.zero = -1
#> ValueError: Zero is definitely greater than your value.
```

> ⓘ If the value does not pass validation, not only will an exception be thrown, but the value will also not be saved for that field. This is similar to how [constraints](https://en.wikipedia.org/wiki/Check_constraint) work in databases.

> ⓘ Validation occurs after [type checking](#type-checking), so you can be sure that types match when your validation function is called.

All values are validated, including default values. However, sometimes you may need to disable validation only for default values, for example, if you use some identifiers for the absence of real values ([`None`](https://docs.python.org/3/library/constants.html#None), [`MISSING`](https://docs.python.org/3/library/dataclasses.html#dataclasses.MISSING), [`NaN`](https://docs.python.org/3/library/math.html#math.isnan), an empty string, or something similar). In this case, pass `True` as the `validate_default` argument:

```python
class PatientsCard(Storage):
    had_rubella: bool | None = Field(
        None,
        validation: lambda x: isinstance(x, bool),
        validate_default=False,  # The default value will not be checked.
        doc='we may not know if a person has had rubella, but if we do, then either yes or no',
    )
    ...
```


## Conflicts between fields

Sometimes, individual field values are [acceptable](#validation-of-values), but certain combinations of them are impossible. For such cases, there is a separate type of value check — conflict checking. This validation is a little more complicated than for individual values. To enable it, you need to pass a dictionary as parameter `conflicts`, whose keys are the names of other class fields, and whose values are functions that return `bool`, answering the question «is there a conflict with the value of this field?»:

```python
class Dossier(Storage):
    name: str = Field()
    is_jew: bool | None = Field(None, doc='jews do not eat pork')
    eats_pork: bool | None = Field(
        None,
        conflicts={'is_jew': lambda old, new, other_old, other_new: new is True and (other_old is True or other_new is True)},
    )
    ...
```

When we attempt to redefine the value of a field that has conflict conditions defined with another field, these conditions will be checked and, if a conflict is confirmed, the operation will be stopped by throwing an exception:

```python
dossier = Dossier(name='John')

dossier.is_jew = True
dossier.eats_pork = True
#> ValueError: The new True (bool) value of the "eats_pork" field conflicts with the True (bool) value of the "is_jew" field (jews do not eat pork).
```

> ⓘ Conflict checking only happens after [type](#type-checking) and individual [value checking](#validation-of-values). This means that only values that are guaranteed to be valid in terms of individuality will be passed to your conflict checking function.

> ⓘ More details on this will be provided in the section on [thread safety](#thread-safety), but here it is useful to know that mutexes for fields with specified conflict conditions are combined. This means that checking fields for conflicts is thread-safe.

The function that checks for a conflict with the value of another field takes 4 positional arguments:

- The old value of the current field.
- New value of the current field.
- The old value of the field with which a conflict is possible.
- The new value of the field with which a conflict is possible.

But why can there be two values for another field? The fact is that, by default, conflict conditions are checked when values are changed not only for the field for which they are set, but also for potentially conflicting fields:

```python
dossier.eats_pork = True
dossier.is_jew = True
#> ValueError: The new True (bool) value of the "is_jew" field (jews do not eat pork) conflicts with the True (bool) value of the "eats_pork" field.
```

Reverse checks can be disabled by passing `False` as the `reverse_conflicts` parameter:

```python
    ...
    eats_pork: bool | None = Field(
        None,
        conflicts={'is_jew': lambda old, new, other_old, other_new: new is True and (other_old is True or other_new is True)},
        reverse_conflicts=False,  # Conflicts will now only be checked when the values of this field change, but not when other fields change.
    )
    ...
```

However, I do not recommend disabling reverse checks - they ensure that the contents of the fields are consistent with each other.


## Sources

So far, we have discussed that fields can have default values, as well as values obtained during the program operation. However, there is a third type of value: values loaded from data sources. The library supports several data sources:

- Configuration files in various formats ([`TOML`](#toml-files-and-pyprojecttoml), [`YAML`](#yaml-files), and [`JSON`](#json-files)).
- [Environment variables](#environment-variables).
- [Command line arguments](#cli-interfaces).

The current value of each class field is determined by the following order:

```mermaid
graph TD;
  A[Default values] --> B(Data sources in the order listed) --> C(The values set in the runtime)
```

That is, values obtained from sources have higher priority than default values, but can be overwritten (unless you [prohibit it](#read-only-fields)) by other values at runtime.

There are two ways to specify a list of sources:

- For the **whole class**.
- For a **specific field**.

To specify a list of sources for the entire class, pass it to the class constructor:

```python
from skelet import TOMLSource

class MyClass(Storage, sources=[TOMLSource('pyproject.toml', table='tool.my_tool_name')]):
    ...
```

Also use the `sources` parameter to specify a list of sources for a specific field:

```python
class MyClass(Storage):
    some_field = Field('some_value', sources=[TOMLSource('pyproject.toml', table='tool.my_tool_name')])
```

You can also combine these two options by specifying one list of sources for the class as a whole and another list for a specific field. Keep in mind that in this case, the list of sources for this field will be completely rewritten. If you want this field to use both its own set of sources and the class's list of sources, specify an ellipsis at the end of the list for the field:

```python
class MyClass(Storage, sources=[TOMLSource('pyproject.toml', table='tool.my_tool_name')]):
    some_field = Field('some_value', sources=[TOMLSource('config_for_this_field.toml'), ...])
```

All values from sources are loaded when the config object is created. This means that (theoretically) during program execution, you can, for example, change a configuration file, then create a new storage object, and its contents will be different. The old object will not automatically know that the config file has been changed. Avoid this kind of behavior in your programs if you don't want to run into problems that will be very difficult to detect.

Each data source is a dictionary-like object from which the values of a specific field are retrieved by the key in the form of the field name. If no value is found in any of the sources, only then will the default value be used. The order in which the contents of the sources are checked corresponds to the order in which the sources themselves are listed, with sources for a field having higher priority than sources for the class as a whole.

For any field, you can change the key used to search for its value in the sources using the `alias` parameter:

```python
class MyClass(Storage, sources=[TOMLSource('pyproject.toml', table='tool.my_tool_name')]):
    some_field = Field(alias='another_key')
```

Values obtained from sources are validated in the same way as all others. However, [type checking](#type-checking) for collections is stricter here: the contents of lists, dictionaries, and tuples are checked in their entirety.

Read more about the available types of sources below.


## Environment variables

For many developers, [environment variables](https://en.wikipedia.org/wiki/Environment_variable) are the first method that comes to mind for [obtaining application settings](#sources) from outside sources. To connect environment variables to your class or class field, use the `EnvSource` class:

```python
from skelet import EnvSource

class MyClass(Storage, sources=[EnvSource()]):
    some_field = Field('some_value')
```

By default, environment variables are searched for by key in the form of an attribute name, but the case is ignored. If you want to make the search case-sensitive, pass `True` as the `case_sensitive` parameter:

```python
EnvSource(case_sensitive=True)
```

> ⚠️ On `Windows`, environment variables are case-insensitive, so this setting will not work.

Sometimes you may also want to “personalize” environment variables, i.e., bind them to your application or library using a prefix. For example, you may want the value for the `field_name` attribute to be searched for using the `prefix_` key. In this case, set the appropriate prefix:

```python
EnvSource(prefix='prefix_')  # So, for attribute "field_name", the search will be performed by key "prefix_field_name".
```
Similar to the `prefix`, you can also specify a `postfix` — a piece of the key that will be added at the end:

```python
EnvSource(postfix='_postfix')  # For attribute "field_name", the search will be performed by key "field_name_postfix".
```

> ⓘ It is important to understand that `EnvSource` objects cache all environment variable values. A complete cache of all variables is created when the key is searched for the first time. Currently, there is no option to clear the cache; the object can only be replaced entirely.

Environment variables can be used to store values of only certain data types. The initial strings are converted to final values based on type hints for specific fields. Here are the supported options:

- `str`- any string can be interpreted as a `str` type. If you used the `Any` annotation for the field or did not specify annotations at all, the value will also be interpreted as a string.
- `int` - any integers.
- `float` - any floating-point numbers, including infinities and [`NaN`](https://en.wikipedia.org/wiki/NaN).
- `bool`- the strings `"yes"`, `"True"`, and `"true"` are interpreted as `True`, while `"no"`, `"False"`, or `"false"` are interpreted as `False`.
- `date` or `datetime` - strings representing, respectively, dates or dates + time in [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) format.
- `list` - lists in [`json`](https://en.wikipedia.org/wiki/JSON) format are expected.
- `tuple` - lists in [`json`](https://en.wikipedia.org/wiki/JSON) format are expected.
- `dict` - dicts in [`json`](https://en.wikipedia.org/wiki/JSON) format are expected.


## TOML files and pyproject.toml

The [`TOML`](https://toml.io/en/) format is currently the most preferred file format for storing application settings for Python. It is very easy to interpret in programming languages in dictionary-like structures, and it is also minimalistic and easy to read.

To read the configuration from a specific file, create a `TOMLSource` object passing the file name or a [Path-like object](https://docs.python.org/3/library/pathlib.html#basic-use) to the constructor:

```python
from skelet import TOMLSource

class MyClass(Storage, sources=[TOMLSource('my_config.toml')]):
    ...
```

The `TOML` format supports so-called “[tables](https://toml.io/en/v1.0.0#table)” — sections of the configuration that are converted into nested hash tables when read. By default, we read the top-level table, but we can also read one of the nested tables. To do this, use the `table` parameter:

```python
TOMLSource('my_config.toml', table='first_level.second_level')  # Instead of a dot-delimited string, you can also pass a list of strings.
```

> ⓘ If you are writing your own library and allowing users to configure it via a [`pyproject.toml`](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) file, it is generally recommended to use table `tool.<your library name>` for this purpose.

> ⓘ All file contents are cached after the first value is read.


## JSON files

If you need config files, I recommend using the [`TOML`](#toml-files-and-pyprojecttoml) format. However, if for some reason you are using [`JSON`](https://en.wikipedia.org/wiki/JSON), it can also be connected as a [source](#sources) using class `JSONSource`:

```python
from skelet import JSONSource

class MyClass(Storage, sources=[JSONSource('my_config.json')]):
    ...
```

Everything will work similarly to reading [`TOML` files](#toml-files-and-pyprojecttoml), except that tables are not supported here.


## YAML files

[YAML](https://en.wikipedia.org/wiki/YAML) is a popular format for storing configurations. I recommend choosing [`TOML`](#toml-files-and-pyprojecttoml) if you have the option, but if not, use the `YAMLSource` class:

```python
from skelet import YAMLSource

class MyClass(Storage, sources=[YAMLSource('my_config.yaml')]):
    ...
```

Everything also will work similarly to reading [`TOML` files](#toml-files-and-pyprojecttoml), except that tables are not supported here.


## CLI interfaces

`skelet` can automatically parse command line arguments. To do this, use the `FixedCLISource` object, to which you need to pass a list of positional and/or named command line arguments:

```python
#!/usr/bin/env python3
# Obviously, this is not a completed program, just a fragment of the code in it.

from skelet import FixedCLISource

class MyClass(Storage, sources=[
    FixedCLISource(
        named_arguments=['first_field', 'second_field'],
        position_arguments=['third_field'],
    ),
]):
    first_field: str = Field('default')
    second_field: str = Field('default')
    third_field: str = Field('default')
```

Now we can run our script, and the arguments that we pass will automatically fill in the corresponding fields of our class:

```bash
./our_script.py --first-field value "positional argument"
```

As you can see, names of positional arguments require adding two hyphens at the beginning, like this: `--`, and also all the underscores should also be replaced with hyphens. If the field name consists of 1 character, only 1 hyphen should be added at the beginning.

If a specific named field has a `bool` type hint, it does not need to pass any value. The rest of the fields need it, and they will be interpreted according to their type hints.

All arguments are optional, and if they are not present on the command line, just the default value will be used. The positional arguments are filled in exactly in the order in which you listed them, and if any of them is missing, it will be interpreted as if the last one is missing. For this reason, I do not recommend defining more than one positional command line argument.


## Collecting sources

Often, you may want to connect not one, but several different sources for your settings. For example, you may need to combine settings from [environment variables](#environment-variables) and settings from the [`pyproject.toml` file](#toml-files-and-pyprojecttoml), with environment variables having higher priority. The straightforward way to implement this would be to pass multiple source objects to the class, as discussed [above](#sources). However, there is also a way to configure this automatically using the `for_tool` function:

```python
from skelet import for_tool

class MyClass(Storage, sources=for_tool('my_tool_name')):
    ...
```

*How does it work?* This function automatically aggregates a set of sources in the following priority (the higher in the list, the higher the priority):

- [Environment variables](#environment-variables) with the prefix `<my_tool_name>_`.
- Files `<my_tool_name>.toml` and `.<my_tool_name>.toml`.
- Section `tool.<my_tool_name>` of [`pyproject.toml` file](#toml-files-and-pyprojecttoml) file.
- Files `<my_tool_name>.yaml` and `.<my_tool_name>.yaml`.
- Files `<my_tool_name>.json` and `.<my_tool_name>.json`.

If the file does not exist, it will simply be ignored.


## Converting values

Sometimes you may need to store data in a format other than the one the user code is trying to save it in. In this case, pass the converter function as argument `conversion`:

```python
class Digits(Storage):
    my_favorite_digit: int | str = Field(
        0,
        conversion=lambda x: {
            'zero': 0,
            'one': 1,
            'two': 2,
            'three': 3,
            'four': 4,
            'five': 5,
            'six': 6,
            'seven': 7,
            'eight': 8,
            'nine': 9,
        }.get(x, x),
        validation=lambda x: x is not None and x >= 0 and x < 10,
        doc='my favorite number from 0 to 9',
    )

digits = Digits()

digits.my_favorite_digit = 'two'
print(digits.my_favorite_digit)
#> 2
```

> ⓘ Values are fully validated ([type](#type-checking) and [individual value validation](#validation-of-values)) before and after conversion. If the conversion changes the type of the value, either do not use a type hint at all, or [use one](#type-checking) that includes both types.


## Thread safety

Thread security is an important priority in the development of `skelet`.

All write operations are protected by mutexes by default, with individual mutexes used for each field. A primitive form of transactionality is used here: if a value fails type checking or other checks, it is not applied, and other threads cannot read the “incorrect” value at that time: the new value will only become available once all checks have been passed. If you specify conditions for [checking conflicts](#conflicts-between-fields) between two different fields, they start using the same mutex to ensure that there are no races.

According to [Amdahl's law](https://en.wikipedia.org/wiki/Amdahl%27s_law), the benefits of program parallelization decrease dramatically as the proportion of execution time that occurs under a mutex increases. Therefore, the `skelet` library uses a mutex only for a critical operation: replacing one value with another, but it does not use it, for example, during the value verification phase.

The key parts of thread safety are reliably tested.


## Callbacks for changes

You can specify an arbitrary code that will be applied when the value of a specific field is changed. This only works if it was changed directly from the program code, and not, for example, by replacing the configuration file that is used as a [source](#sources).

> ⓘ If you assign a value to the field that is equal to the value that this field had before, the callback will not be called.

To use this, pass a function that takes 3 positional arguments:

- Old field value.
- New field value.
- Config object.

> ⓘ Be careful when accessing other fields in the config object; try not to catch a [deadlock](https://en.wikipedia.org/wiki/Deadlock_(computer_science)).

Example:

```python
class MyClass(Storage):
    field: int = Field(0, change_action=lambda old, new, storage: print(f'{old} -> {new}'))

storage = MyClass()

storage.field = 5
#> 0 -> 5
storage.field = 55
#> 5 -> 55
```

> ⓘ The callback will be called only if the new value passes all the checks. The callback call is closed by the field mutex: two callbacks for the same field of the same object cannot be executed simultaneously. Thus, the callback call is completely [thread-safe](#thread-safety).


## Read only fields

You can protect individual fields from being able to change their values. To do this, pass `read_only=True` to the field constructor:

```python
class EternalTruths(Storage):
    inevitability: str = Field('Two things are certain: death and taxes', read_only=True)

storage = EternalTruths()

print(storage.inevitability)
#> Two things are certain: death and taxe
storage.inevitability = 'There are a lot of unavoidable things.'
#> AttributeError: "inevitability" field is read-only.
```

> ⓘ This restriction only applies to user code. Default values and loading values from sources will continue to function.


## Transformations and serialization

Application settings are rarely selected «outside»; usually, they do not need to be sent over the network or anything like that. But if you suddenly need to do so, you can convert such an object into a standard Python format for serialization, [`dict`](https://docs.python.org/3/library/stdtypes.html#typesmapping), using the `asdict()` function:

```python
from skelet import asdict

class FlyingСonfig(Storage):
    some_field: int = Field(42)

data = asdict(FlyingСonfig())
print(data)
#> {'some_field': 42}
```

After completing this conversion, you can continue to treat the data as a regular `dict`, for example, convert it to `JSON` and send it over the network.
