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

Pip will also install the executable scripts `czytget`, which runs a
czytget server and an integrated client with an own command shell.

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

### Version 1.0: first release

#### Non-breaking

First complete implementation of library `czytget`, which includes
module `server` (the server), module `client` (an integrated client
that communicates directly with the server via direct messaging) and
module `ytconnector` (an interface to the `yt-dlp` backend the server
uses to perform downloads).

### Version 1.1

#### Non-breaking

Downloaded files now timestamped with the download time instead of the source's
upload time.
