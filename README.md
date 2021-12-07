# czytget

A simple server to execute multiple parallel download jobs.


## Installation

### The quick way

Change into  the root directory  of this distribution (where  the file
`pyproject.toml` is) and run the following command:

```shell
pip install .
```

This will install  the library **czytget** at a  location where python
will  find it,  independently of  which directory  you're in  when you
invoke python.

To access the functionality of the library from within the interactive
Python console or from another Python application, import it with

```python
import czytget
```

Documentation can be accessed with `help(czytget)`.

Pip will also install the executable scripts `czytgetd` and `czytget`.

If you are not *root* when  you run the installation command, Pip will
install the library and executables locally in your home.

To undo the installation, simply do:

```shell
pip uninstall czytget
```

### The manual way

1. Copy or move the directory  `src/czytget` to any location you like,
   for example `$HOME/python/czytget`.

2. Continuing with this example, add `$HOME/python` to the environment
   variable `PYTHONPATH`.

3. Copy  or  move  the  executable scripts  located  in  `bin` to  any
   location you like, for example `$HOME/bin`.

4. Make sure that `$HOME/bin` is in your `PATH` variable.


## Changelog

### Version 1.0.0: first release

#### Non-breaking additions
