# Dynamic registry

## Usage

### With `setup.py`

Here is the format to use in the `entry_points` section of your `setup.py`:

```python
        entry_points={
            "group": [
                "unique_string=plugin_module:super_class",
            ]
        }
```

* `group`: an arbitrary name that identifies a set of plugins that you want to 
  retrieve (e.g., one set for input plugins, another for output plugins)
* `unique_string`: an arbitrary, unique string that identifies this line
* `plugin_module`: the name of the module that contains the plugins
* `super_class`: the fully qualified superclass name that the plugins need to belong to 


### Without `setup.py`

While developing your plugins, you will want to test them. However, unless
you install your library in a virtual environment, the entry points from your
`setup.py` won't be available. 

To avoid having to install the library just for some tests, you have two options:

* You can supply a default list of modules to check for classes (`default_modules`)
* You can define an environment variable with a comma-separated list of
  modules to check for classes (`env_modules`)

Both can be supplied as arguments when instantiating the `seppl.Registry`
registry class, with the environment variable taking precedence over the
default modules list.


## Example

Below is a toy example of how to make use of the `seppl` library
(the full code is available from the 
[seppl-example repository](https://github.com/waikato-datamining/seppl-example)).

### Plugins

The following plugins have been defined in the [my.plugins](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/plugins.py) 
module:

```python
import argparse
from seppl import Plugin


class SomePlugin(Plugin):

    def name(self) -> str:
        return "some-plugin"

    def description(self) -> str:
        return "This description is being used for the argparse description."

    def _create_argparser(self) -> argparse.ArgumentParser:
        parser = super()._create_argparser()
        parser.add_argument("-i", "--input_file", type=str, help="A file to read", required=True)
        return parser

    def _apply_args(self, ns: argparse.Namespace):
        super()._apply_args(ns)
        self.input_file = ns.input_file


class OtherPlugin(Plugin):

    def name(self) -> str:
        return "other"

    def description(self) -> str:
        return "Another plugin, this time without any additional command-line arguments."


class Dud(Plugin):

    def name(self) -> str:
        return "dud"

    def description(self) -> str:
        return "Dummy plugin."
```

### `setup.py`

Add a custom entry point to the `entry_points` section of your [setup.py](https://github.com/waikato-datamining/seppl-example/blob/main/setup_dynamic.py) 
and list the plugin modules and the associated superclass, e.g.:

```python
    entry_points={
        "myplugins": [
            "plugins=my.plugins:seppl.Plugin",
        ],
    }
```

### Instantiating a registry

You can instantiate a `seppl.Registry` singleton as follows (e.g., in the 
[my.registry](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/registry.py) 
module in your project):

```python
from seppl import Registry, MODE_DYNAMIC

# the default modules to look for plugins
MY_DEFAULT_MODULES = ",".join(
    [
        "my.plugins",
    ])

# the environment variable to use for overriding the default modules
# (comma-separated list)
MY_ENV_MODULES = "MY_MODULES"

# the entry point group to use in setup.py for the plugins.
ENTRYPOINT_MYPLUGINS = "myplugins"

# singleton of the Registry (in dynamic mode)
REGISTRY = Registry(mode=MODE_DYNAMIC,
                    default_modules=MY_DEFAULT_MODULES,
                    env_modules=MY_ENV_MODULES,
                    enforce_uniqueness=True)
```

### Using the registry

#### Retrieving plugins

[Retrieving the plugins](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/retrieve_plugins.py) 
using the following code:

```python
from my.registry import REGISTRY, ENTRYPOINT_MYPLUGINS
from seppl import Plugin

plugins = REGISTRY.plugins(ENTRYPOINT_MYPLUGINS, Plugin)
for p in plugins:
    print(plugins[p].name())
```

Will produce something like this:

```
dud
other
some-plugin
```


#### Parsing a command-line

[Parsing a command-line](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/parse_cmdline.py)
with the following code:


```python
from my.registry import REGISTRY, ENTRYPOINT_MYPLUGINS
from seppl import Plugin, split_cmdline, split_args, args_to_objects

cmdline = "other some-plugin -i /some/where/blah.txt dud"
plugins = REGISTRY.plugins(ENTRYPOINT_MYPLUGINS, Plugin)
args = split_args(split_cmdline(cmdline), plugins.keys())
parsed = args_to_objects(args, plugins, allow_global_options=False)
for p in parsed:
    print(p)
```

Will output something like this:

```
<my.plugins.OtherPlugin object at 0x7f638cc13610>
<my.plugins.SomePlugin object at 0x7f638cc13be0>
<my.plugins.Dud object at 0x7f638cc13c10>
```

**NB:** The `allow_global_options` determines whether you can have options 
preceding any plugin (hence *global* options).


#### Generating help screens

Automatically [generating documentation](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/generate_help.py) 
for the plugins is also a useful feature. The following code generates
a [Markdown](https://daringfireball.net/projects/markdown/) file for each of 
the plugins in the current directory:

```python
from my.registry import REGISTRY, ENTRYPOINT_MYPLUGINS
from seppl import Plugin, generate_help, HELP_FORMAT_MARKDOWN

plugins = REGISTRY.plugins(ENTRYPOINT_MYPLUGINS, Plugin)
# this will generate markdown files for each of the plugins in the current directory
generate_help(plugins.values(), help_format=HELP_FORMAT_MARKDOWN,
              output_path="..")
```
