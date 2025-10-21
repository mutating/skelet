![logo](https://raw.githubusercontent.com/pomponchik/skelet/develop/docs/assets/logo_8.svg)

Collect all the settings in one place


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

To do:

- [ ] Checking fields for conflicts
- [ ] The ability to disable type checking for a class through class arguments
- [ ] The specified sections in the `pyproject.toml` file
- [ ] One or more separate `toml` files
- [ ] The ability to share a single mutex into several fields
- [ ] Converting types from one to another
- [ ] Subtraction of environment variables
- [ ] Class inheritance support
- [ ] Reading parameters from the CLI
- [ ] Context manager like https://confz.readthedocs.io/en/latest/usage/context_manager.html
- [ ] 'yaml' format support
- [ ] 'json' format support
- [ ] Special classes for checking through types for belonging to sets of positive or natural numbers


Links to add here:

- https://www.reddit.com/r/Python/comments/10zdidm/why_type_hinting_sucks/
