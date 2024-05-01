# seppl
<img align="right" src="img/seppl_logo.png" width="15%"/>

Simple Entry Point PipeLines (**seppl**). Python library for parsing pipeline 
components with their own options. 

**seppl** takes a very light-weight approach to avoid encroaching too much on
your code. If you want to, you can add some compatibility checks between the 
pipeline components (see further down).
However, the execution of the pipeline (and potentially moving data between 
components) is left to you and your code.


## Installation

### PyPI

```bash
pip install seppl 
```

### Github

```bash
pip install git+https://github.com/waikato-datamining/seppl.git
```


## Usage

### Registry

*seppl* can operate in three different modes:

* [class lister registry](docs/class_lister_registry.md) - a single function (aka class lister) returns a dictionary  
  of superclasses and their associated modules (slower, due to analyzing code) 
* [dynamic registry](docs/dynamic_registry.md) - only superclass and module need to be supplied for initializing 
  a plugin class hierarchy (slower, due to analyzing code)
* [explicit registry](docs/explicit_registry.md) - every single plugin needs to be listed (fast)


### Plugins

Your plugins need to be derived from the `seppl.Plugin` superclass, for the
*magic* to work. Such a plugin needs to implement the following two methods:

* `name(self)`: returns the name/identifier to use in the pipeline command string 
  (potentially followed by options for the plugin to parse)
* `description(self)`: returns a description (how long is up to you), which is used
  for the argparse parser; the same parser that can be used to generate a help
  screen for a plugin

In order to have custom options parsed by your plugin, you need to override
the following two methods:

* `_create_argparser(self)`: this method assembles the argparse parser
* `_apply_args(self, ns: argparse.Namespace)`: in this method, you need to 
  transfer the parsed options into member variables of your plugin 


### Compatibility

If you want to enable checks between pipeline components, then your plugins
need to implement the appropriate mixins and implement the relevant methods:

* `seppl.OutputProducer`: for plugins that generate data; the `generates` method
  returns a list of classes that the plugin can output (typically only one).
* `seppl.InputConsumer`: for plugins that consume data; the `accepts` method
  returns a list of classes that the plugin can process.

E.g., *reader* plugins would implement `OutputProducer`, *filters* would 
implement both, `OutputProducer` and `InputConsumer`, and *writers* only
`InputConsumer`.

You can then run the `check_compatibility` method against your pipeline,
i.e., a list of plugins, to see whether they are compatible. This method will
raise an exception if plugins are not implementing the mixins or if there is
no overlap between the generated/accepted classes.

For general purpose plugins, you can use `AnyData` dummy class in the
`accepts`/`generates` methods, as this class is used by default as a 
*match all* by the `check_compatibility` method.

See the plugins in [plugins_comp.py](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/plugins_comp.py)
and [some example pipeline checks](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/compatibility.py)
done with them. 


### Unicode characters

The following methods can be used for escaping/unescaping unicode characters
to make them copyable into remote ssh sessions:

* `seppl.escape_args`
* `seppl.unescape_args`


### Tools

The following command-line tools are available:

* `seppl-escape`: for escaping unicode characters
* `seppl-unescape`: for unescaping unicode characters
