# skelet
Collect all the settings in one place


One object with a configuration for your project.

It's ready now::

- [x] Default values specified in the class
- [x] Values that are set during operation for class attributes
- [x] Read only fields

To do:

- [ ] Typing support
- [ ] Checking field names (prohibit underscores at the beginning)
- [ ] Documenting fields
- [ ] The specified sections in the `pyproject.toml` file
- [ ] One or more separate `toml` files
- [ ] The ability to validate any fields (+ a set of standard validators for basic field types)
- [ ] The ability to set a callback to change any of the fields + a mutex to a mutable field to ensure thread safety)
- [ ] A separate mutex for each field
- [ ] The ability to share a single mutex into several fields
- [ ] Checking fields for conflicts
- [ ] Converting types from one to another
- [ ] Subtraction of environment variables
- [ ] Class inheritance support
- [ ] Reading parameters from the CLI
- [ ] Context manager like https://confz.readthedocs.io/en/latest/usage/context_manager.html
- [ ] Secret fields
- [ ] 'yaml' format support
- [ ] 'json' format support
- [ ] The ability to turn-off thread safety
- [ ] The ability to disable type checking for a class through class arguments


Links to add here:

- https://www.reddit.com/r/Python/comments/10zdidm/why_type_hinting_sucks/
