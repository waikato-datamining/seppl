Changelog
=========

0.1.1 (2024-02-07)
------------------

- `check_compatibility` method now also checks whether generated class is
  subclass of accepted classes, to allow for broader `accepts()` methods
- `gcd` method now creates a copy of the integer ratio list before processing it


0.1.0 (2024-02-05)
------------------

- added basic support for meta-data: MetaDataHandler, get_metadata, add_metadata
- added support for splitting sequences using supplied (int) split ratios
- added session support: Session, SessionHandler
- added I/O super classes: Reader, Writer, StreamWriter, BatchWriter, Filter, MultiFilter
- added support for executing I/O pipelines: Reader, [Filter...], [Writer]


0.0.11 (2023-11-27)
-------------------

- the `DEFAULT` placeholder in the environment variable listing the modules now
  gets expanded to the default modules, making it easier to specify modules
  in derived projects
- added `excluded_modules` and `excluded_env_modules` to `Registry` class
  initializer to allow user to specify modules (explicit list or list from env
  variable) to be excluded from being registered; useful when outputting
  help for derived modules that shouldn't output all the base plugins as well.


0.0.10 (2023-11-15)
-------------------

- the registry now inspects modules when environment modules are present even when
  it already found plugins (eg default ones)


0.0.9 (2023-11-15)
------------------

- the registry now inspects modules when custom modules were supplied even when
  it already found plugins (eg default ones)


0.0.8 (2023-11-10)
------------------

- suppressing help output for unknown args now


0.0.7 (2023-11-09)
------------------

- `Plugin.parse_args` now returns any unparsed arguments that were found
- the `args_to_objects` method now raises an Exception by default when
  unknown arguments are encountered for a plugin (can be controlled with
  the `allow_unknown_args` parameter)


0.0.6 (2023-10-11)
------------------

- enforcement of uniqueness is now checking whether the class names differ
  before raising an exception.


0.0.5 (2023-10-10)
------------------

- added `OutputProducer` and `InputConsumer` mixins that can be use for checking
  the compatibility between pipeline components using the `check_compatibility`
  function.


0.0.4 (2023-10-09)
------------------

- added support for `dynamic` mode which only requires listing the superclass of a plugin
  and the module in which to look for these plugins (slower, but more convenient)


0.0.3 (2023-10-05)
------------------

- added `generate_entry_points` helper method to easily generate the `entry_points` section
  for plugins, rather than manually maintaining it
- added `generate_help` and `generate_plugin_usage` methods for generating documentation
  for plugins


0.0.2 (2023-10-04)
------------------

- removed old, logging-related code from Plugin class
- added `args_to_objects` to quickly instantiate plugins from parsed arguments
- added example to README.md and example library (https://github.com/waikato-datamining/seppl-example)


0.0.1 (2023-09-28)
------------------

- initial release

