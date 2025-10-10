# skelet
Collect all the settings in one place


One object with a configuration for your project. This can take settings away from:

- [x] Default values specified in the class
- [x] Values that are set during operation for class attributes
- [x] Read only fields
- [ ] Typing support
- [ ] The specified sections in the `pyproject.toml` file
- [ ] One or more separate `toml` files

Additional features:

- [ ] The ability to validate any fields (+ a set of standard validators for basic field types)
- [ ] The ability to set a callback to change any of the fields + a mutex to a mutable field to ensure thread safety)
- [ ] A separate mutex for each field
- [ ] The ability to share a single mutex into several fields
- [ ] Checking fields for conflicts
- [ ] Converting types from one to another
- [ ] Subtraction of environment variables
- [ ] Nested classes
- [ ] Reading parameters from the CLI
- [ ] Context manager like https://confz.readthedocs.io/en/latest/usage/context_manager.html
- [ ] Secret fields
- [ ] 'yaml' format support
- [ ] 'json' format support
- [ ] Turn-off thread safety
