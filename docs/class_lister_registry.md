# Class lister registry

## Usage

### With `setup.py`

Here is the format to use in the `entry_points` section of your `setup.py`:

```python
        entry_points={
            "class_lister": [
                "unique_string=module_name:function_name",
            ]
        }
```

Notes:
* `class_lister`: is the name the `ClassListerRegistry` looks for to identify class lister functions
* `:function_name`: can be omitted, as long as the function name defaults to `list_classes`


### Without `setup.py`

While developing your plugins, you will want to test them. However, unless
you install your library in a virtual environment, the entry points from your
`setup.py` won't be available. 

To avoid having to install the library just for some tests, you have two options:

* You can supply a default list of class listers to retrieve the classes from (`default_class_listers`)
* You can define an environment variable with a comma-separated list of
  class listers to use (`env_class_listers`)

Both can be supplied as arguments when instantiating the `seppl.ClassListerRegistry`
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

Add a custom entry point to the `entry_points` section of your [setup.py](https://github.com/waikato-datamining/seppl-example/blob/main/setup_class_lister.py) 
and list the plugin modules and the associated superclass, e.g.:

```python
    entry_points={
        "class_lister": [
            "myplugins=my.plugins.class_lister",
        ],
    }
```

### Instantiating a registry

You can instantiate a `seppl.ClassListerRegistry` singleton as follows (e.g., in the 
[my.class_lister_registry](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/class_lister_registry.py) 
module in your project):

```python
from seppl import ClassListerRegistry

# the default class lister
MY_DEFAULT_CLASS_LISTERS = "my.class_lister"

# the environment variable to use for overriding the default modules
# (comma-separated list)
MY_ENV_CLASS_LISTERS = "MY_CLASS_LISTERS"

# singleton of the Registry
REGISTRY = ClassListerRegistry(default_class_listers=MY_DEFAULT_CLASS_LISTERS,
                               env_class_listers=MY_ENV_CLASS_LISTERS)
```

### Using the registry

#### Retrieving plugins

[Retrieving the plugins](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/retrieve_plugins_class_lister.py) 
using the following code:

```python
from my.class_lister_registry import REGISTRY
from seppl import Plugin

plugins = REGISTRY.plugins(Plugin)
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

[Parsing a command-line](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/parse_cmdline_class_lister.py)
with the following code:


```python
from my.class_lister_registry import REGISTRY
from seppl import Plugin, split_cmdline, split_args, args_to_objects

cmdline = "other some-plugin -i /some/where/blah.txt dud"
plugins = REGISTRY.plugins(Plugin)
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

Automatically [generating documentation](https://github.com/waikato-datamining/seppl-example/blob/main/src/my/usage/generate_help_class_lister.py) 
for the plugins is also a useful feature. The following code generates
a [Markdown](https://daringfireball.net/projects/markdown/) file for each of 
the plugins in the current directory:

```python
from my.class_lister_registry import REGISTRY
from seppl import Plugin, generate_help, HELP_FORMAT_MARKDOWN

plugins = REGISTRY.plugins(Plugin)
# this will generate markdown files for each of the plugins in the current directory
generate_help(plugins.values(), help_format=HELP_FORMAT_MARKDOWN,
              output_path="..")
```

### Advanced usage

#### Ignoring classes 

When inheriting plugins from other libraries, not all of them may be applicable
in the current application's context. The `ClassListerRegistry` therefore
allows you to specify class lister functions that return the full class names
of classes to ignore.

The following class lister (`my.class_lister_ignored`) returns a single 
class name of a plugin to be ignored:

```python
from typing import List, Dict


def list_classes() -> Dict[str, List[str]]:
    return {
        "seppl.Plugin": [
            "my.plugins.UselessPlugin",
        ],
    }
```

```python
from seppl import ClassListerRegistry

# the default class lister
MY_DEFAULT_CLASS_LISTERS = "my.class_lister"

# the environment variable to use for overriding the default modules
# (comma-separated list)
MY_ENV_CLASS_LISTERS = "MY_CLASS_LISTERS"

# the default class lister
MY_DEFAULT_CLASS_LISTERS_IGNORED = "my.class_lister_ignored"

# the environment variable to use for overriding the default modules
# (comma-separated list)
MY_ENV_CLASS_LISTERS_IGNORED = "MY_CLASS_LISTERS_IGNORED"

# singleton of the Registry
REGISTRY = ClassListerRegistry(default_class_listers=MY_DEFAULT_CLASS_LISTERS,
                               env_class_listers=MY_ENV_CLASS_LISTERS,
                               ignored_class_listers=MY_DEFAULT_CLASS_LISTERS_IGNORED,
                               env_ignored_class_listers=MY_ENV_CLASS_LISTERS_IGNORED)
```

#### Excluding class listers 

When developing multi-module applications, generating the documentation for
sub-modules should not necessarily include the plugins from super-modules.

When instantiating the `ClassListerRegistry` object, you can therefore
specify the class name(s) of the class listers to exclude via the 
`excluded_class_listers` parameter of the constructor. The parameter
`env_excluded_class_listers` can be used to specify an environment variable
that contains the comma-separated list of class names of the class listers 
to exclude.
