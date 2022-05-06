Contributing
===============
Please read these guidelines before contributing to the project.

------------------------------

### Table of Contents
- [Styleguide](#styleguide)
     - [Naming Conventions](#naming-conventions)
     - [Modules](#modules)
     - [Imports](#imports)

Styleguide
---------------

### Naming Conventions
Python:
   - **camelCase** Qt slots and signals

   - **PascalCase** Classes
   - **PascalCase** MetaClasses
   - **PascalCase** Type Aliases

   - **snake_case** Functions
   - **snake_case** Methods
   - **snake_case** Modules
   - **snake_case** Packages
   - **snake_case** Properties
   - **snake_case** Variables

   - **SCREAMING_SNAKE_CASE** Constants

Markdown:
   - `=` for h1
   - `-` for h2
   - `**` for bold
   - `_` for italic


### Modules
Copyright headers, docstrings, and an `__all__` attribute are mandatory.

Order of module elements:

1. Shebang line, if included.

2. Copyright header

3. Module's docstring

4. Dunder variables (ex: `__all__`)

5. Imports

6. Constants

7. Functions

8. Classes

9. `if __name__ == '__main__':` entrypoint

Full Example:
```python
#!/usr/bin/env python
############################
# License and copyright text
############################
"""This is a module's docstring."""

__all__ = (
   'CONSTANT',
   'foo',
   'Foo',
)

from foo import Bar

CONSTANT = 1

def foo():
   """This is a function's docstring."""

class Foo(Bar):
   """This is a class's docstring."""

if __name__ == '__main__':
   foo()
```


### Imports

`__all__` should be a tuple containing the module's public attributes, ordered alphabetically.

Imports should be formatted as follows:

1. Modules from the stdlib
    1. module imports
    2. `from` imports

2. External modules (included in the project's requirements)
    1. module imports
    2. `from` imports

3. Local modules
    - Parent packages should be placed above their child packages
    - Module imports should be placed above their package's `from` imports
    1. `from` imports from a parent package
    2. `from` imports from the current package

Other rules:

- The main three categories should be separated by line breaks.

- All imports should be on a single line, and should be sorted alphabetically.

- All local imports should be relative imports. Ex: `from .module import Class` as opposed to `from module import Class`.

- When importing multiple attributes from a module, each line should contain one import. Ex:
   ```python
   from module import attribute
   from module import other_attribute
   ```

- Only `import *` modules which have an `__all__` attribute defined.

Full Example:
```python
import os
from pathlib import Path

import external_module
from other_external_module import external_function

from ...parents_parent_package_module import a1
from .. import parent_package_module
from ..other_parent_package_module import b1
from ..other_parent_package_module import b2
from . import current_package_module
from .another_current_package_module import c1
from .other_current_package_module import *
```
