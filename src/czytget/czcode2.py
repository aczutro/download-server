# Copyright (C) 2005 - present  Alexander Czutro <github@czutro.ch>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# For more details, see the provided licence file or
# <http://www.gnu.org/licenses>.
#
################################################################### aczutro ###

"""Help functions for code generation."""


def autoRepr(cls):
    """
    Decorator: auto-generates __repr__ method for the given class.
    """
    cls.__repr__ = lambda self : \
        "%s { %s }" \
        % (type(self).__name__,
           ", ".join("%s=%s" % dictEntry for dictEntry in vars(self).items()))
    return cls
#autoRepr


def nop(*args) -> None:
    """Does nothing, with arguments.

    Intended to "consume" unused function arguments so as to avoid IDE warnings.
    """
    pass
#nop


### aczutro ###################################################################
