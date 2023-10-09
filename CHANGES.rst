Changelog
=========

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

