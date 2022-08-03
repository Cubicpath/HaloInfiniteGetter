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

| Attribute Type       | Python               | PowerShell |
|----------------------|----------------------|------------|
| Qt slots and signals | camelCase            |            |
| Classes              | PascalCase           | PascalCase |
| MetaClasses          | PascalCase           |            |
| Type Aliases         | PascalCase           |            |
| Functions            | snake_case           | Verb-Noun  |
| Methods              | snake_case           | PascalCase |
| Modules              | snake_case           | PascalCase |
| Packages             | snake_case           |            |
| Parameters           | snake_case           | PascalCase |
| Properties           | snake_case           | PascalCase |
| Variables            | snake_case           | PascalCase |
| Constants            | SCREAMING_SNAKE_CASE | PascalCase |
| Generics             | PascalT_lower_co     |            |

| Convention Type      | Examples                  |
|----------------------|---------------------------|
| lowercase            | foo, foobar, foobarbiz    |
| UPPERCASE            | FOO, FOOBAR, FOOBARBIZ    |
| camelCase            | foo, fooBar, fooBarBiz    |
| PascalCase           | Foo, FooBar, FooBarBiz    |
| snake_case           | foo, foo_bar, foo_bar_biz |
| SCREAMING_SNAKE_CASE | FOO, FOO_BAR, FOO_BAR_BIZ |
| PascalT_lower_co     | FT, BarT_co, FT_covar     |
| Verb-Noun            | New-Shortcut, Get-Value   |


### Modules
Copyright headers, docstrings, and an `__all__` attribute are mandatory.

Order of module elements:

1. Shebang line, if included.

2. Copyright header

3. Module's docstring

4. Any `from __future__` imports

5. Dunder variables (ex: `__all__`)

6. Imports

7. Constants

8. Functions

9. Classes

10. `if __name__ == '__main__':` entrypoint

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

`__all__` should be a tuple containing the module's public attributes meant for import, ordered alphabetically.

`__future__` imports are not to be grouped with other imports, and should be right below the module docstring.

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
